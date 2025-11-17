"""
Agent Installer API
Generate and serve agent installer scripts with embedded code
"""

from flask import request, Response
from binary.dashboard.api import api
from binary.dashboard.models import Agent
from binary.dashboard.database import get_pg_session
from cryptography.fernet import Fernet
import logging
import os
import base64
import glob

logger = logging.getLogger(__name__)

def get_agent_files():
    """Read all agent Python files and encode as base64"""
    agent_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bin', 'agent')

    files = {}

    # Check if agent directory exists
    if not os.path.exists(agent_dir):
        logger.warning(f"Agent directory not found: {agent_dir}")
        # Return empty dict - installer will create placeholder
        return files

    # Get all Python files recursively
    for filepath in glob.glob(os.path.join(agent_dir, '**', '*.py'), recursive=True):
        # Get relative path from agent directory
        rel_path = os.path.relpath(filepath, agent_dir)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Store with relative path as key
                files[rel_path] = content
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")

    return files

def generate_token():
    """Generate encrypted token for agent"""
    key = Fernet.generate_key()
    return base64.b64encode(key).decode('utf-8')

@api.route('/agent/install.sh', methods=['GET'])
def get_installer():
    """
    Generate agent installer script with embedded code

    Query parameters:
        - token: Pre-generated encrypted token (required)
        - name: Agent name (optional, defaults to hostname)
        - tags: Comma-separated tags (optional)
        - agent_id: Agent ID from database (optional)
    """

    token = request.args.get('token')
    if not token:
        return Response(
            "Error: Missing required parameter 'token'",
            status=400,
            mimetype='text/plain'
        )

    name = request.args.get('name', '$(hostname)')
    tags = request.args.get('tags', '')
    agent_id = request.args.get('agent_id', '')

    dashboard_url = request.host_url.rstrip('/')

    # Get all agent files
    agent_files = get_agent_files()

    # Build embedded files section
    if agent_files:
        embedded_files = ""
        for filepath, content in agent_files.items():
            embedded_files += f'''
# File: {filepath}
cat > /opt/suricata-agent/{filepath} << 'AGENT_FILE_EOF'
{content}
AGENT_FILE_EOF

'''
    else:
        # No agent files found - create placeholder
        embedded_files = '''
# Agent files not found in dashboard
# Creating placeholder agent script
cat > /opt/suricata-agent/agent.py << 'AGENT_FILE_EOF'
#!/opt/suricata-agent/venv/bin/python
"""
Suricata Dashboard Agent - Placeholder
Agent files are not yet implemented in the dashboard.
This is a placeholder script that will be replaced when agent code is available.
"""
import sys
import time

print("=" * 60)
print("Suricata Dashboard Agent - Placeholder")
print("=" * 60)
print()
print("Agent files are not yet implemented in the dashboard.")
print("This placeholder keeps the service running while you develop the agent.")
print()
print("The agent will idle until proper agent code is deployed.")
print("=" * 60)

# Keep service running (prevents systemd restart loop)
while True:
    time.sleep(60)
    print("Agent placeholder still running... (waiting for real agent code)")
AGENT_FILE_EOF

'''

    # Generate installer script
    script = f'''#!/bin/bash
#
# Suricata Dashboard Agent Installer
# Generated from: {dashboard_url}
# Agent: {name}
#
# This script installs and configures the Suricata monitoring agent.
# Run with: sudo bash install.sh
#

set -e

# Color output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Suricata Dashboard Agent Installer                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Dashboard: {dashboard_url}"
echo "Agent Name: {name}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${{RED}}✗ Error: Please run as root (use sudo)${{NC}}"
    exit 1
fi

echo -e "${{GREEN}}✓${{NC}} Running as root"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    echo -e "${{RED}}✗ Cannot detect OS${{NC}}"
    exit 1
fi

echo -e "${{GREEN}}✓${{NC}} Detected OS: $OS $VERSION"

# Install dependencies based on OS
echo ""
echo "Installing dependencies..."

case $OS in
    ubuntu|debian)
        apt-get update -qq
        apt-get install -y python3 python3-pip python3-venv sqlite3
        ;;
    centos|rhel|fedora)
        yum install -y python3 python3-pip sqlite
        ;;
    *)
        echo -e "${{YELLOW}}⚠ Warning: Unsupported OS, attempting to continue...${{NC}}"
        ;;
esac

echo -e "${{GREEN}}✓${{NC}} System dependencies installed"

# Create directories
echo ""
echo "Creating directories..."
mkdir -p /opt/suricata-agent/core
mkdir -p /opt/suricata-agent/transport
mkdir -p /etc/suricata-agent
mkdir -p /var/lib/suricata-agent
mkdir -p /var/log/suricata-agent

echo -e "${{GREEN}}✓${{NC}} Directories created"

# Create Python virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv /opt/suricata-agent/venv

echo -e "${{GREEN}}✓${{NC}} Virtual environment created"

# Install Python dependencies
echo ""
echo "Installing Python packages..."
/opt/suricata-agent/venv/bin/pip install --quiet --upgrade pip
/opt/suricata-agent/venv/bin/pip install --quiet requests PyYAML watchdog websocket-client python-socketio cryptography psutil

echo -e "${{GREEN}}✓${{NC}} Python packages installed"

# Write agent files
echo ""
echo "Installing agent files..."

{embedded_files}

# Make agent executable
chmod +x /opt/suricata-agent/agent.py

echo -e "${{GREEN}}✓${{NC}} Agent files installed"

# Create configuration
echo ""
echo "Creating configuration..."

cat > /etc/suricata-agent/config.yaml << 'CONFIG_EOF'
agent:
  name: "{name}"
  token: "{token}"
  tags: [{tags}]

dashboard:
  url: "{dashboard_url}"
  api_version: "v1"
  verify_ssl: true

suricata:
  eve_log: /var/log/suricata/eve.json
  suricata_log: /var/log/suricata/suricata.log
  config_file: /etc/suricata/suricata.yaml

buffer:
  database: /var/lib/suricata-agent/buffer.db
  max_events: 100000

logging:
  level: INFO
  file: /var/log/suricata-agent/agent.log
CONFIG_EOF

chmod 600 /etc/suricata-agent/config.yaml
echo -e "${{GREEN}}✓${{NC}} Configuration created"

# Create systemd service
echo ""
echo "Creating systemd service..."

cat > /etc/systemd/system/suricata-agent.service << 'SERVICE_EOF'
[Unit]
Description=Suricata Dashboard Agent
Documentation=https://github.com/yourusername/suricata-dashboard
After=network.target suricata.service
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/suricata-agent
ExecStart=/opt/suricata-agent/venv/bin/python /opt/suricata-agent/agent.py --config /etc/suricata-agent/config.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SERVICE_EOF

echo -e "${{GREEN}}✓${{NC}} Systemd service created"

# Enable and start service
echo ""
echo "Starting agent service..."

systemctl daemon-reload
systemctl enable suricata-agent
systemctl start suricata-agent

sleep 2

# Check status
if systemctl is-active --quiet suricata-agent; then
    echo -e "${{GREEN}}✓${{NC}} Agent service started successfully"
else
    echo -e "${{RED}}✗${{NC}} Agent service failed to start"
    echo ""
    echo "Check logs with:"
    echo "  journalctl -u suricata-agent -n 50"
    exit 1
fi

# Final message
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║            Installation Complete!                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Agent Information:"
echo "  Name: {name}"
echo "  Dashboard: {dashboard_url}"
echo "  Status: $(systemctl is-active suricata-agent)"
echo ""
echo "Useful commands:"
echo "  systemctl status suricata-agent    # Check service status"
echo "  journalctl -u suricata-agent -f    # Follow logs"
echo "  systemctl restart suricata-agent   # Restart service"
echo ""
echo "Agent will automatically connect to the dashboard."
echo "Check the dashboard UI to verify connection."
echo ""
'''

    return Response(
        script,
        mimetype='text/x-shellscript',
        headers={
            'Content-Disposition': f'attachment; filename=install-suricata-agent-{name.replace(" ", "-")}.sh'
        }
    )
