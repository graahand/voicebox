# VoiceBox + MC-Master UI Integration

This integration connects the VoiceBox backend (Python) with the MC-Master frontend (React) for a complete AI voice assistant experience with animated 3D avatar.

## Architecture

- **Backend**: FastAPI WebSocket server (`api_server.py`)
- **Frontend**: React + Three.js UI (`mc-master/`)
- **Communication**: WebSocket for real-time bidirectional communication

## Features

✅ **Text Input**: Type messages and get AI responses with TTS audio  
✅ **Voice Input**: Record voice messages with automatic STT transcription  
✅ **Real-time State Sync**: Avatar states (idle, speaking, listening) sync automatically  
✅ **3D Avatar Animation**: React-Three-Fiber animated avatar with blinking, speaking, and listening states  
✅ **Audio Playback**: Automatic TTS audio playback in browser  
✅ **Connection Status**: Visual indicators for connection state  
✅ **Theme Support**: Multiple color themes (Ruby, Spectrum)

## Quick Start

### Option 1: Automatic Launch (Recommended)

```bash
./start_integrated.sh
```

This script will:
1. Create/activate Python virtual environment
2. Install dependencies (if needed)
3. Start the backend API server on port 8000
4. Start the frontend dev server on port 5173
5. Monitor both processes

Access the UI at: **http://localhost:5173**

### Option 2: Manual Launch

**Terminal 1 - Backend:**
```bash
# Activate virtual environment
source venv/bin/activate

# Install API dependencies
pip install -r api_requirements.txt

# Start API server
python api_server.py
```

**Terminal 2 - Frontend:**
```bash
cd mc-master
npm install  # First time only
npm run dev
```

## Usage

### Text Interaction
1. Open http://localhost:5173 in your browser
2. Wait for "Connected" status
3. Type your message in the text input field
4. Click "SEND" or press Enter
5. Watch the avatar animate while speaking
6. Audio response plays automatically

### Voice Interaction
1. Click the "VOICE" button (🎤)
2. Speak your message (records for 5 seconds)
3. Avatar switches to "listening" state
4. After recording, STT transcribes your speech
5. AI generates response and avatar speaks

### Manual State Control
Use the MODE buttons to manually control avatar state (for testing):
- **IDLE**: Standby mode with ambient animations
- **SPEAK**: Speaking animation with mouth movement
- **LISTEN**: Listening animation with pulse effects

## API Endpoints

### WebSocket: `ws://localhost:8000/ws`

**Client → Server Messages:**

```json
// Text input
{
  "type": "text_input",
  "text": "Hello, how are you?"
}

// Audio input (base64 encoded)
{
  "type": "audio_input",
  "audio": "base64_encoded_audio_data"
}

// Get status
{
  "type": "get_status"
}

// Manual state change (testing)
{
  "type": "state_change",
  "state": "idle|speaking|listening"
}
```

**Server → Client Messages:**

```json
// State change notification
{
  "type": "state_change",
  "state": "idle|speaking|listening"
}

// Response with audio
{
  "type": "response",
  "data": {
    "success": true,
    "response_text": "AI response text",
    "audio_data": "base64_encoded_wav_audio",
    "transcribed_text": "Your speech (if audio input)",
    "metadata": {}
  }
}

// Status update
{
  "type": "status",
  "data": {
    "initialized": true,
    "current_state": "idle",
    "statistics": {}
  }
}
```

### REST Endpoints:

- `GET /` - API info
- `GET /health` - Health check
- `GET /status` - Current status

## Project Structure

```
test_voicebox/
├── api_server.py              # FastAPI WebSocket server
├── api_requirements.txt       # Backend API dependencies
├── start_integrated.sh        # Integration launcher script
├── README_INTEGRATION.md      # This file
├── main.py                    # Original VoiceBox CLI
├── config/                    # Configuration
├── modules/                   # VoiceBox modules
│   ├── llm_handler.py
│   ├── tts_handler.py
│   ├── stt_handler.py
│   └── ...
└── mc-master/                 # Frontend UI
    ├── src/
    │   ├── App.jsx           # Main app component
    │   ├── services/
    │   │   └── voiceboxApi.js  # WebSocket client
    │   └── components/
    │       ├── Avatar.jsx    # 3D animated avatar
    │       ├── ControlPanel.jsx  # UI controls
    │       └── ...
    └── package.json
```

## Configuration

### Backend Configuration

Edit `config/config.py` or `.env` file:
- `TAVILY_API_KEY` - For web search functionality
- `PICOVOICE_ACCESS_KEY` - For wake word detection (optional)

### Feature Toggles

In `api_server.py`, the VoiceBox service initializes with:
- LLM: ✓ Enabled
- RAG: ✓ Enabled  
- Search: ✓ Enabled
- STT: ✓ Enabled
- TTS: ✓ Enabled

### Frontend Configuration

Default WebSocket URL: `ws://localhost:8000/ws`

To change, edit `mc-master/src/App.jsx`:
```javascript
await voiceboxApi.connect('ws://your-server:8000/ws')
```

## Troubleshooting

### Backend Won't Start
- Check Python dependencies: `pip install -r api_requirements.txt`
- Check if port 8000 is available: `lsof -i :8000`
- View logs: `tail -f logs/backend.log`

### Frontend Won't Start
- Install dependencies: `cd mc-master && npm install`
- Check if port 5173 is available: `lsof -i :5173`
- View logs: `tail -f logs/frontend.log`

### WebSocket Connection Failed
- Ensure backend is running and healthy: `curl http://localhost:8000/health`
- Check browser console for error messages
- Verify WebSocket URL is correct

### Audio Not Playing
- Check browser permissions for audio
- Look for audio errors in browser console
- Verify TTS is generating audio (check backend logs)

### Microphone Not Working
- Grant microphone permissions in browser
- Check browser console for getUserMedia errors
- Test microphone in browser: chrome://settings/content/microphone

## Development

### Backend Development
```bash
# Install in development mode
pip install -e .

# Run with auto-reload
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd mc-master
npm run dev  # Vite dev server with hot reload
```

### Testing WebSocket
Use a WebSocket client like `websocat`:
```bash
websocat ws://localhost:8000/ws
```

## Performance Tips

1. **Optimize Audio**: TTS generates WAV files; consider converting to MP3 for bandwidth
2. **Caching**: Enable LLM response caching for common queries
3. **Batch Processing**: Queue multiple requests during high load
4. **Resource Limits**: Set max concurrent WebSocket connections

## Future Enhancements

- [ ] Add user authentication
- [ ] Support multiple simultaneous users
- [ ] Add conversation history panel
- [ ] Implement audio streaming (real-time TTS)
- [ ] Add video avatar option
- [ ] Mobile-responsive design
- [ ] Docker containerization
- [ ] Production deployment guide

## License

Same as parent VoiceBox project.

## Credits

- **VoiceBox Backend**: Original Python implementation
- **MC-Master UI**: React + Three.js frontend
- **Integration**: WebSocket bridge layer

---

**Need Help?** Check logs in `logs/` directory or open an issue.
