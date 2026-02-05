"""
VoiceBox WebSocket API Server
Provides WebSocket API for the frontend UI to interact with VoiceBox.
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Set
import base64
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config.config import Config
from config.logger import get_logger, suppress_library_warnings
from modules.llm_handler import LLMHandler
from modules.tts_handler import TTSHandler
from modules.stt_handler import STTHandler
from modules.conversation_manager import ConversationManager
from modules.response_formatter import ResponseFormatter

# Suppress third-party library warnings
suppress_library_warnings()

logger = get_logger('api_server')

app = FastAPI(title="VoiceBox API", version="1.0.0")

# CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


class VoiceBoxService:
    """Service class to manage VoiceBox components and state."""
    
    def __init__(self):
        self.llm: Optional[LLMHandler] = None
        self.tts: Optional[TTSHandler] = None
        self.stt: Optional[STTHandler] = None
        self.conversation: Optional[ConversationManager] = None
        self.formatter: Optional[ResponseFormatter] = None
        self.current_state: str = 'idle'
        self.is_initialized: bool = False
        
    async def initialize(self):
        """Initialize all VoiceBox components."""
        if self.is_initialized:
            return
            
        try:
            logger.info("Initializing VoiceBox Service...")
            Config.ensure_directories()
            
            # Initialize components
            self.llm = LLMHandler()
            # Enable RAG and Search after initialization
            self.llm.set_rag_enabled(True)
            self.llm.set_search_enabled(True)
            logger.info("LLM Handler initialized")
            
            self.tts = TTSHandler()
            logger.info("TTS Handler initialized")
            
            self.stt = STTHandler()
            logger.info("STT Handler initialized")
            
            self.conversation = ConversationManager()
            logger.info("Conversation Manager initialized")
            
            self.formatter = ResponseFormatter()
            logger.info("Response Formatter initialized")
            
            self.is_initialized = True
            logger.info("VoiceBox Service fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize VoiceBox Service: {e}", exc_info=True)
            raise
    
    async def process_text(self, text: str) -> Dict:
        """Process text input and generate response with audio."""
        if not self.is_initialized:
            logger.error("Service not initialized")
            return {
                'success': False,
                'error': 'Service is still initializing. Please wait.'
            }
        
        try:
            self.current_state = 'speaking'
            await broadcast_state('speaking')
            
            # Generate LLM response (returns tuple of response_text, attributions)
            logger.info(f"Processing text: {text}")
            llm_response, attributions = self.llm.generate_response(
                user_input=text,
                conversation_history=self.conversation.get_conversation_history()
            )
            
            # Format response for TTS (returns formatted string)
            response_text = self.formatter.format_full_response(llm_response)
            
            # Log conversation
            self.conversation.add_user_message(text)
            self.conversation.add_assistant_message(response_text)
            
            # Generate audio using generate_and_save (returns Path or None)
            audio_filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            audio_path = self.tts.generate_and_save(response_text, audio_filename)
            
            # Read audio file and encode to base64
            audio_data = None
            if audio_path and audio_path.exists():
                with open(audio_path, 'rb') as f:
                    audio_bytes = f.read()
                    audio_data = base64.b64encode(audio_bytes).decode('utf-8')
                # Clean up temp file
                audio_path.unlink()
            
            # Don't set idle here - let the frontend manage state during audio playback
            # The frontend will set idle after audio finishes playing
            self.current_state = 'idle'
            # Only broadcast idle if there's no audio (frontend will handle it otherwise)
            if not audio_data:
                await broadcast_state('idle')
            
            return {
                'success': True,
                'response_text': response_text,
                'audio_data': audio_data,
                'metadata': {'attributions': attributions} if attributions else {}
            }
            
        except Exception as e:
            logger.error(f"Error processing text: {e}", exc_info=True)
            self.current_state = 'idle'
            await broadcast_state('idle')
            return {
                'success': False,
                'error': str(e)
            }
    
    async def process_audio(self, audio_data: bytes) -> Dict:
        """Process audio input (speech to text, then generate response)."""
        if not self.is_initialized:
            logger.error("Service not initialized")
            return {
                'success': False,
                'error': 'Service is still initializing. Please wait.'
            }
        
        try:
            self.current_state = 'listening'
            await broadcast_state('listening')
            
            # Save audio to temporary file
            temp_audio_path = Config.AUDIO_DIR / f"temp_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            with open(temp_audio_path, 'wb') as f:
                f.write(audio_data)
            
            # Transcribe audio (returns tuple of text, info_dict)
            logger.info("Transcribing audio...")
            transcribed_text, stt_info = self.stt.transcribe_audio(temp_audio_path)
            
            # Clean up temp file
            if temp_audio_path.exists():
                temp_audio_path.unlink()
            
            if not transcribed_text:
                self.current_state = 'idle'
                await broadcast_state('idle')
                return {
                    'success': False,
                    'error': 'Failed to transcribe audio'
                }
            
            logger.info(f"Transcribed: {transcribed_text}")
            
            # Process the transcribed text
            result = await self.process_text(transcribed_text)
            result['transcribed_text'] = transcribed_text
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            self.current_state = 'idle'
            await broadcast_state('idle')
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_status(self) -> Dict:
        """Get current status of the service."""
        return {
            'initialized': self.is_initialized,
            'current_state': self.current_state,
            'statistics': self.conversation.get_statistics() if self.conversation else {}
        }


# Global service instance
voicebox_service = VoiceBoxService()


async def broadcast_state(state: str):
    """Broadcast state change to all connected clients."""
    message = json.dumps({
        'type': 'state_change',
        'state': state
    })
    
    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.warning(f"Failed to send to connection: {e}")
            disconnected.add(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        active_connections.discard(conn)


@app.on_event("startup")
async def startup_event():
    """Initialize the VoiceBox service on startup."""
    try:
        await voicebox_service.initialize()
        logger.info("API Server started successfully")
        
        # Notify all connected clients that initialization is complete
        await broadcast_state('idle')
        
    except Exception as e:
        logger.error(f"Failed to start API server: {e}", exc_info=True)
        # Continue running to allow clients to see the error status


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "VoiceBox API Server", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "initialized": voicebox_service.is_initialized
    }


@app.get("/status")
async def get_status():
    """Get current status."""
    return voicebox_service.get_status()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"New WebSocket connection. Total connections: {len(active_connections)}")
    
    try:
        # Send initial status
        status = voicebox_service.get_status()
        await websocket.send_json({
            'type': 'status',
            'data': status
        })
        
        # Warn client if not initialized
        if not voicebox_service.is_initialized:
            await websocket.send_json({
                'type': 'error',
                'data': {'message': 'Service is still initializing. Please wait.'}
            })
        
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            data = json.loads(message)
            
            msg_type = data.get('type')
            
            if msg_type == 'text_input':
                # Process text input
                text = data.get('text', '')
                logger.info(f"Received text input: {text}")
                
                result = await voicebox_service.process_text(text)
                
                await websocket.send_json({
                    'type': 'response',
                    'data': result
                })
                
            elif msg_type == 'audio_input':
                # Process audio input (base64 encoded)
                audio_b64 = data.get('audio', '')
                audio_bytes = base64.b64decode(audio_b64)
                logger.info(f"Received audio input: {len(audio_bytes)} bytes")
                
                result = await voicebox_service.process_audio(audio_bytes)
                
                await websocket.send_json({
                    'type': 'response',
                    'data': result
                })
                
            elif msg_type == 'get_status':
                # Send current status
                await websocket.send_json({
                    'type': 'status',
                    'data': voicebox_service.get_status()
                })
                
            elif msg_type == 'state_change':
                # Manual state change from UI (for testing)
                state = data.get('state', 'idle')
                voicebox_service.current_state = state
                await broadcast_state(state)
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        active_connections.discard(websocket)
        logger.info(f"Connection closed. Total connections: {len(active_connections)}")


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server."""
    logger.info(f"Starting VoiceBox API Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
