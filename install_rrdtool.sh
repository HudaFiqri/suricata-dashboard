#!/bin/bash

echo "Installing RRDtool dependencies..."

# Detect OS
if [ -f /etc/debian_version ]; then
    echo "Detected Debian/Ubuntu"
    sudo apt-get update
    sudo apt-get install -y librrd-dev libpython3-dev
elif [ -f /etc/redhat-release ]; then
    echo "Detected RHEL/CentOS/Fedora"
    sudo yum install -y rrdtool-devel python3-devel
elif [ -f /etc/arch-release ]; then
    echo "Detected Arch Linux"
    sudo pacman -S --noconfirm rrdtool
else
    echo "Unknown OS. Please install rrdtool development libraries manually."
    exit 1

if [ $? -eq 0 ]; then
    echo "✓ RRDtool installed successfully!"
else
    echo "✗ Failed to install rrdtool. Monitoring features will be disabled."
    echo "   The application will still work without RRDtool."
fi
