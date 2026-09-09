#!/bin/bash
set -e

echo "Installing wget and gdebi-core..."
sudo apt-get update
sudo apt-get install -y wget gdebi-core

echo "Downloading and installing devkitpro-pacman..."
if ! wget -U "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" https://apt.devkitpro.org/install-devkitpro-pacman; then
    echo "=========================================================================="
    echo "ERROR: Cloudflare is blocking the download (403 Forbidden)."
    echo "Please open this URL in your web browser to bypass the block:"
    echo "  https://apt.devkitpro.org/install-devkitpro-pacman"
    echo ""
    echo "Save the page as 'install-devkitpro-pacman' in this directory,"
    echo "then run this install_linux.sh script again."
    echo "=========================================================================="
    exit 1
fi

chmod +x ./install-devkitpro-pacman
sudo ./install-devkitpro-pacman

echo "Installing GBA toolchain (gba-dev)..."
sudo dkp-pacman -S --noconfirm gba-dev

echo "Installing mGBA for testing..."
sudo apt-get install -y mgba-sdl mgba-qt

echo "Done! You can now build the project by running 'make'"
