FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user (optional, currently agent runs as root)
# RUN useradd -m -u 1000 suricata && chown -R suricata:suricata /app
# USER suricata

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/v1/health')"

# Run migrations and start app
CMD python binary/tools/migrations/migrate.py up && \
    gunicorn --worker-class gevent \
             --workers 4 \
             --bind 0.0.0.0:5000 \
             --timeout 120 \
             --access-logfile - \
             --error-logfile - \
             wsgi:app
