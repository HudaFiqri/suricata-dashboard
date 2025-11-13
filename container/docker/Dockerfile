# Suricata Dashboard - Production Docker Image
FROM python:3.11-slim-bookworm

LABEL maintainer="Suricata Dashboard"
LABEL description="Lightweight web dashboard for Suricata IDS/IPS monitoring"
LABEL version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
# - librrd-dev: RRDtool library for monitoring graphs
# - libpq-dev: PostgreSQL client library
# - default-libmysqlclient-dev: MySQL client library
# - build-essential: Compilation tools for Python packages
# - curl: Health check utility
RUN apt-get update && apt-get install -y --no-install-recommends \
    librrd-dev \
    libpq-dev \
    default-libmysqlclient-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directories
RUN useradd -m -u 1000 -s /bin/bash suricata && \
    mkdir -p /app /opt/suricata_monitoring/data /opt/suricata_monitoring/log && \
    chown -R suricata:suricata /app /opt/suricata_monitoring

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY --chown=suricata:suricata requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=suricata:suricata . .

# Create directories for application data
RUN mkdir -p \
    /opt/suricata_monitoring/data \
    /opt/suricata_monitoring/log \
    /var/lib/suricata/rrd && \
    chown -R suricata:suricata \
    /opt/suricata_monitoring \
    /var/lib/suricata

# Switch to non-root user
USER suricata

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Run the application
CMD ["python", "run.py"]
