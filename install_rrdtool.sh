#!/usr/bin/env bash
set -euo pipefail

echo "Installing RRDtool build dependencies..."

# Detect OS
if [ -f /etc/debian_version ]; then
    echo "Detected Debian/Ubuntu"
    sudo apt-get update
    # Headers + toolchain + pkg-config for detecting rrdtool
    sudo apt-get install -y rrdtool librrd-dev python3-dev build-essential pkg-config
elif [ -f /etc/redhat-release ]; then
    echo "Detected RHEL/CentOS/Fedora"
    # Toolchain + headers
    if command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y rrdtool rrdtool-devel python3-devel gcc make pkgconfig
    else
        sudo yum install -y rrdtool rrdtool-devel python3-devel gcc make pkgconfig
    fi
elif [ -f /etc/arch-release ]; then
    echo "Detected Arch Linux"
    sudo pacman -Syu --noconfirm rrdtool base-devel pkgconf python
else
    echo "Unknown OS. Please install RRDtool dev libraries and a compiler toolchain manually."
    echo "Required: rrdtool, librrd-dev/rrdtool-devel, python3-dev, gcc/make, pkg-config"
    exit 1
fi

echo "Installing Python rrdtool package..."
pip install rrdtool==0.1.16

echo "RRDtool Python package installed. Graphing features enabled."

