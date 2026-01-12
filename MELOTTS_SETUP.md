# MeloTTS Setup Guide

This document provides detailed instructions for setting up MeloTTS in the VoiceBox project.

## Quick Installation

### Option 1: Using the Installation Script (Recommended)

```bash
chmod +x install_melotts.sh
./install_melotts.sh
```

### Option 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/myshell-ai/MeloTTS.git
cd MeloTTS

# Install in editable mode
pip install -e .

# Download the unidic dictionary (required for Japanese text processing)
python -m unidic download

# Go back to project root
cd ..
```

## Configuration

MeloTTS settings can be configured in [`config/config.py`](config/config.py):

```python
# TTS settings (MeloTTS)
TTS_LANGUAGE: str = "EN"          # Language code: EN, ES, FR, ZH, JP, KR
TTS_SPEAKER: str = "EN-US"        # Speaker/accent
TTS_SPEED: float = 1.0            # Speech speed (0.5 = slower, 2.0 = faster)
TTS_DEVICE: str = "auto"          # 'auto', 'cpu', 'cuda', 'cuda:0', 'mps'
```

## Available Speakers (English)

- `EN-US` - American English accent
- `EN-BR` - British English accent  
- `EN_INDIA` - Indian English accent
- `EN-AU` - Australian English accent
- `EN-Default` - Default English accent

## Supported Languages

MeloTTS supports multiple languages:
- **EN** - English
- **ES** - Spanish
- **FR** - French
- **ZH** - Chinese
- **JP** - Japanese
- **KR** - Korean

## Usage Examples

### Basic Usage

```python
from modules.tts_handler import TTSHandler
from pathlib import Path

# Initialize handler (singleton)
tts = TTSHandler()

# Generate speech with default settings
audio_path = tts.generate_and_save(
    text="Hello, this is a test.",
    filename="output.wav"
)
```

### Using Different Accents

```python
# American accent
tts.generate_and_save(
    text="Did you ever hear a folk tale about a giant turtle?",
    filename="american.wav",
    speaker="EN-US"
)

# British accent
tts.generate_and_save(
    text="Did you ever hear a folk tale about a giant turtle?",
    filename="british.wav",
    speaker="EN-BR"
)

# Indian accent
tts.generate_and_save(
    text="Did you ever hear a folk tale about a giant turtle?",
    filename="indian.wav",
    speaker="EN_INDIA"
)
```

### Adjusting Speech Speed

```python
# Slower speech (0.5x)
tts.generate_and_save(
    text="This is slower speech.",
    filename="slow.wav",
    speed=0.5
)

# Faster speech (1.5x)
tts.generate_and_save(
    text="This is faster speech.",
    filename="fast.wav",
    speed=1.5
)
```

## Docker Setup

### Dockerfile with MeloTTS

```dockerfile
FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    espeak-ng \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone and install MeloTTS
RUN git clone https://github.com/myshell-ai/MeloTTS.git /tmp/MeloTTS && \
    cd /tmp/MeloTTS && \
    pip install -e . && \
    python -m unidic download && \
    rm -rf /tmp/MeloTTS

# Copy and install project requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

CMD ["python", "main.py"]
```

### Building and Running

```bash
# Build
docker build -t voicebox:melotts .

# Run
docker run -it --rm \
  --runtime nvidia \
  --network host \
  --device /dev/snd \
  -v $(pwd)/data:/app/data \
  voicebox:melotts
```

## Troubleshooting

### Issue: "No module named 'melo'"

**Solution**: Install MeloTTS properly
```bash
git clone https://github.com/myshell-ai/MeloTTS.git
cd MeloTTS
pip install -e .
```

### Issue: "No module named 'unidic'"

**Solution**: Download the unidic dictionary
```bash
python -m unidic download
```

Or install unidic-lite (lighter version):
```bash
pip install unidic-lite
```

### Issue: MeCab errors

**Solution**: Install system MeCab dependencies
```bash
# Ubuntu/Debian
sudo apt-get install mecab libmecab-dev mecab-ipadic-utf8

# macOS
brew install mecab mecab-ipadic
```

### Issue: Slow inference on Jetson

**Solution**: Ensure CUDA is being used
```python
# In config.py
TTS_DEVICE = "cuda"  # Force CUDA usage
```

Check GPU usage:
```bash
sudo tegrastats
```

### Issue: Audio quality issues

**Solution**: Try adjusting the speed parameter
```python
# Slightly slower speed often improves quality
tts.generate_and_save(text, filename, speed=0.9)
```

## Performance Tips

1. **First Run**: The first inference is slower due to model loading. Subsequent calls are faster.

2. **Device Selection**: 
   - `auto` - Automatically selects GPU if available
   - `cuda` - Force GPU usage (fastest)
   - `cpu` - Force CPU usage (slower but more compatible)

3. **Batch Processing**: If generating multiple audio files, reuse the same TTSHandler instance (it's a singleton).

4. **Memory**: MeloTTS uses approximately 1-2GB of RAM when loaded.

## References

- [MeloTTS GitHub Repository](https://github.com/myshell-ai/MeloTTS)
- [MeloTTS Documentation](https://github.com/myshell-ai/MeloTTS/blob/main/README.md)
- [Paper: MeloTTS - High-quality Multi-lingual Text-to-Speech Library](https://arxiv.org/abs/2404.02790)
