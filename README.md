# VoiceBox

An interactive voice assistant powered by AI, combining Large Language Models (LLM), Text-to-Speech (TTS), and Speech-to-Text (STT) technologies.

## Overview

VoiceBox is an interactive voice assistant that integrates:
- **LLM Backend**: Ollama with SmolLM2 for intelligent conversation
- **Text-to-Speech**: KokoroTTS for natural voice synthesis
- **Speech-to-Text**: faster-whisper for accurate transcription with VAD
- **Conversation Management**: JSON-based logging with timestamps and metadata

Developed by Skill Museum.

## Features

- **Modular Architecture**: Clean, maintainable code with singleton pattern for resource management
- **Conversational AI**: Context-aware responses using SmolLM2
- **Natural Speech**: High-quality voice synthesis with KokoroTTS
- **Accurate Transcription**: Fast speech recognition with Voice Activity Detection
- **Conversation Logging**: Automatic JSON logging with timestamps and statistics
- **Response Formatting**: Optimized text formatting for natural-sounding speech
- **Interactive Mode**: Real-time text-based conversation interface

## Project Structure

```
test_voicebox/
├── config/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   └── system_prompt.txt      # System prompt for LLM
├── modules/
│   ├── __init__.py
│   ├── llm_handler.py         # LLM integration (Ollama)
│   ├── tts_handler.py         # Text-to-Speech (KokoroTTS)
│   ├── stt_handler.py         # Speech-to-Text (faster-whisper)
│   ├── conversation_manager.py # Conversation history & logging
│   └── response_formatter.py  # Response text formatting
├── data/
│   ├── audio/                 # Generated audio files
│   └── conversations/         # Conversation logs (JSON)
├── logs/                      # Application logs
├── main.py                    # Main controller
├── requirements.txt           # Python dependencies
├── plan.md                    # Project plan and specifications
└── README.md                  # This file
```

## Requirements

- Python 3.8+
- CUDA-compatible GPU (recommended for faster-whisper)
- Ollama installed and running
- espeak-ng (for KokoroTTS)

## Installation

### 1. Install System Dependencies

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install espeak-ng
```

#### On macOS:
```bash
brew install espeak
```

### 2. Install Ollama

Follow instructions at [Ollama.ai](https://ollama.ai) to install Ollama for your system.

### 3. Pull the LLM Model

```bash
ollama pull smollm2:latest
```

### 4. Install Python Dependencies

```bash
cd test_voicebox
pip install -r requirements.txt
```

## Configuration

The project uses a centralized configuration system in [config/config.py](config/config.py). Key settings include:

- **LLM Model**: `smollm2:latest`
- **TTS Voice**: `af_heart`
- **STT Model**: `large-v3`
- **Max Response Length**: 200 tokens
- **Temperature**: 0.7

Edit these settings in the Config class as needed.

## Usage

### Interactive Text Mode

Run the main application for interactive text-based conversations:

```bash
python main.py
```

Commands:
- Type your message and press Enter
- `stats` - Display conversation statistics
- `quit`, `exit`, or `q` - End conversation and save logs

### Using Individual Modules

Each module can be tested independently:

```bash
# Test LLM Handler
python modules/llm_handler.py

# Test TTS Handler
python modules/tts_handler.py

# Test STT Handler
python modules/stt_handler.py

# Test Conversation Manager
python modules/conversation_manager.py

# Test Response Formatter
python modules/response_formatter.py
```

### Processing Audio Files

To process audio input (STT -> LLM -> TTS):

```python
from main import VoiceBoxController
from pathlib import Path

controller = VoiceBoxController()
transcribed, response, audio_path = controller.process_audio_input(
    Path("path/to/audio.mp3")
)
```

## Python Best Practices Implemented

1.  **Entry Points**: All scripts have `if __name__ == '__main__':` blocks
2. **Type Annotations**: Comprehensive type hints for all functions and variables
3. **Function Simplicity**: Single-responsibility functions with clear return types
4.  **List Comprehensions**: Used where applicable for concise code
5.  **Enumerate**: Used instead of range for iteration
6.  **Singleton Pattern**: Resource-intensive components use singleton instances
7.  **Modular Architecture**: Clean separation of concerns
8.  **Data-Driven Rules**: Validation rules as data structures (see response_formatter.py)
9.  **Pathlib**: Cross-platform file path handling
10.  **Properties**: Private attributes exposed via `@property` decorators
11.  **Docstrings**: Comprehensive documentation for all functions

## Output Files

### Audio Files
Generated audio responses are saved in `data/audio/` with timestamps:
- Format: `response_YYYYMMDD_HHMMSS.wav`
- Sample Rate: 24000 Hz

### Conversation Logs
Conversations are saved in `data/conversations/` as JSON:
- Format: `session_YYYYMMDD_HHMMSS.json`
- Contains: Full conversation history, timestamps, response times, and metadata

Example log structure:
```json
{
  "session_id": "session_20260111_123456",
  "session_start": "2026-01-11T12:34:56",
  "session_end": "2026-01-11T12:45:30",
  "total_interactions": 5,
  "conversation_history": [...],
  "interaction_log": [
    {
      "timestamp": "2026-01-11T12:35:00",
      "user_query": "Hello",
      "model_response": "Hi there!",
      "response_time_seconds": 0.523,
      "status": "success"
    }
  ]
}
```

## Architecture

### Singleton Pattern
Resource-intensive components (LLM, TTS, STT) use singleton pattern to ensure only one instance exists:
- Prevents multiple model loadings
- Efficient memory usage
- Consistent state management

### Response Formatting
The response formatter cleans LLM output for natural speech:
- Removes markdown formatting
- Converts symbols to words
- Removes code blocks and links
- Limits response length
- Removes citations

### Conversation Management
Tracks conversation context and metrics:
- Maintains conversation history for context
- Logs all interactions with timestamps
- Calculates response times and success rates
- Generates session statistics

## Troubleshooting

### CUDA/GPU Issues
If you encounter GPU errors with faster-whisper, the system will automatically fallback to CPU:
```python
# Edit config/config.py
STT_DEVICE = "cpu"
STT_COMPUTE_TYPE = "int8"
```

### Ollama Connection Issues
Ensure Ollama is running:
```bash
ollama serve

## Contributing

This project follows strict Python best practices:
- All code must have type annotations
- All functions must have docstrings
- Follow the singleton pattern for resource-intensive components
- Use pathlib for file operations
- Keep functions simple and focused

## License

Developed by Skill Museum.

## Acknowledgments

- **Ollama**: LLM backend framework
- **MeloTTS**: Text-to-Speech engine
- **faster-whisper**: Speech-to-Text engine
- **SmolLM2**: Lightweight language model by Hugging Face
