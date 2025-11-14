#!/usr/bin/env python3
"""
Development Server Runner
For production, use wsgi.py with gunicorn
"""

import sys
import os

def check_dependencies():
    """Check if optional dependencies are installed"""
    missing = []
    warnings = []

    # Check RRDtool
    try:
        import rrdtool
        print("✓ RRDtool is installed - Monitoring features enabled")
    except ImportError:
        warnings.append({
            'name': 'RRDtool',
            'feature': 'Monitoring/Graphing',
            'install': [
                'Install system libraries first:',
                '  Debian/Ubuntu: sudo apt-get install librrd-dev libpython3-dev',
                '  RHEL/CentOS:   sudo yum install rrdtool-devel python3-devel',
                '  Arch Linux:    sudo pacman -S rrdtool',
                '',
                'Then install Python package:',
                '  pip install rrdtool==0.1.16',
                '',
                'Or run: ./install_rrdtool.sh'
            ]
        })
        print("⚠ RRDtool not installed - Monitoring features will be disabled")

    # Check SQLAlchemy
    try:
        import sqlalchemy
        print("✓ SQLAlchemy is installed - Database features enabled")
    except ImportError:
        missing.append({
            'name': 'SQLAlchemy',
            'install': 'pip install SQLAlchemy==2.0.23'
        })

    # Check other required packages
    required = {
        'flask': 'Flask',
        'flask_socketio': 'Flask-SocketIO',
        'flask_cors': 'Flask-CORS',
        'psutil': 'psutil',
        'yaml': 'PyYAML',
        'pymongo': 'pymongo',
        'jwt': 'PyJWT',
        'bcrypt': 'bcrypt',
        'gevent': 'gevent'
    }

    for module, package in required.items():
        try:
            __import__(module)
            print(f"✓ {package} is installed")
        except ImportError:
            missing.append({
                'name': package,
                'install': f'pip install {package}'
            })

    # Print missing dependencies
    if missing:
        print("\n" + "=" * 60)
        print("ERROR: Missing required dependencies!")
        print("=" * 60)
        for dep in missing:
            print(f"\n✗ {dep['name']} is not installed")
            print(f"  Install: {dep['install']}")
        print("\nOr install all at once:")
        print("  pip install -r requirements.txt")
        print("=" * 60)
        return False

    # Print warnings for optional dependencies
    if warnings:
        print("\n" + "=" * 60)
        print("OPTIONAL DEPENDENCIES NOT INSTALLED")
        print("=" * 60)
        for warn in warnings:
            print(f"\n⚠ {warn['name']} - Required for: {warn['feature']}")
            for line in warn['install']:
                print(f"  {line}")
        print("\n" + "=" * 60)
        print("The application will run without these features.")
        print("You can install them later to enable additional functionality.")
        print("=" * 60 + "\n")

    return True

def main():
    # Only show startup banner on main process (not reloader)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("\n" + "=" * 60)
        print("     Suricata Dashboard - Remote Monitoring")
        print("=" * 60)
        print("\nChecking dependencies...")
        print("-" * 60)

        if not check_dependencies():
            print("\nPlease install missing dependencies and try again.")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("Starting development server with WebSocket support...")
        host = os.getenv('FLASK_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_PORT', 5000))
        print(f"Dashboard will be available at: http://{host}:{port}")
        print("WebSocket endpoints:")
        print(f"  - Agent:  ws://{host}:{port}/ws/v1/agent")
        print(f"  - UI:     ws://{host}:{port}/ws/v1/ui")
        print("\nPress Ctrl+C to stop the server")
        print("=" * 60 + "\n")

    try:
        from binary.dashboard import create_app

        app, socketio = create_app()

        # Run with SocketIO (supports WebSocket)
        socketio.run(
            app,
            host=os.getenv('FLASK_HOST', '0.0.0.0'),
            port=int(os.getenv('FLASK_PORT', 5000)),
            debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
