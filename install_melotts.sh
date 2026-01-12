#!/bin/bash

# Installation script for MeloTTS
# This script installs MeloTTS and its dependencies

echo "=========================================="
echo "Installing MeloTTS for VoiceBox"
echo "=========================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed. Please install git first."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install uv first."
    echo "Visit: https://github.com/astral-sh/uv"
    exit 1
fi

# Install PyTorch first (if not already installed)
echo ""
echo "Installing PyTorch with CUDA 12.6 support..."
uv pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126

# Check if MeloTTS directory already exists
if [ -d "MeloTTS" ]; then
    echo ""
    echo "MeloTTS directory already exists. Using existing directory..."
else
    # Clone MeloTTS repository
    echo ""
    echo "Cloning MeloTTS repository..."
    git clone https://github.com/myshell-ai/MeloTTS.git
fi

# Install MeloTTS
echo ""
echo "Installing MeloTTS dependencies..."
cd MeloTTS

# Create a temporary requirements file without torch to avoid reinstallation
echo "Creating filtered requirements (excluding torch)..."
grep -v "^torch" requirements.txt > requirements_filtered.txt

# Install filtered requirements using uv
uv pip install -r requirements_filtered.txt

# Install MeloTTS in editable mode without dependencies (since we already installed them)
echo "Installing MeloTTS package..."
uv pip install -e . --no-deps

# Download unidic
echo ""
echo "Downloading unidic dictionary..."
python -m unidic download

# Go back to the original directory
cd ..

echo ""
echo "=========================================="
echo "MeloTTS installation complete!"
echo "=========================================="
echo ""
echo "You can now run the VoiceBox application."
echo "Try: python main.py"
