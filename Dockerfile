# Using Python Images
FROM python:latest

# Working Directory
WORKDIR /suricata-dashboard

# Copy All Files To Docker Images
COPY . .

# Running Install Python Packages
RUN pip install -r requirements.txt

# Expose Default Port
EXPOSE 80

# Running Suricata Dashboard
CMD ["python3", "run.py"]