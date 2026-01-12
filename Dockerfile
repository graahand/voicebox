FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    espeak-ng \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone and install MeloTTS
RUN echo "Installing MeloTTS..." && \
    git clone https://github.com/myshell-ai/MeloTTS.git /tmp/MeloTTS && \
    cd /tmp/MeloTTS && \
    pip install --no-cache-dir -e . && \
    python -m unidic download && \
    rm -rf /tmp/MeloTTS/.git

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port if needed for future API
EXPOSE 8000

# Run the main application
CMD ["python", "main.py"]
