"""
VoiceBox Main Controller.
Orchestrates all components: LLM, TTS, STT, and conversation management.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple
import time
import subprocess
import tempfile
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config.config import Config
from modules.llm_handler import LLMHandler
from modules.tts_handler import TTSHandler
from modules.stt_handler import STTHandler
from modules.conversation_manager import ConversationManager
from modules.response_formatter import ResponseFormatter


class VoiceBoxController:
    """
    Central controller that orchestrates all VoiceBox components.
    Manages the flow between STT, LLM, TTS, and conversation logging.
    """
    
    def __init__(self) -> None:
        """
        Initialize the VoiceBox controller with all components.
        """
        print("Initializing VoiceBox...")
        
        # Ensure directories exist
        Config.ensure_directories()
        
        # Initialize all components (using singleton pattern)
        self._llm: LLMHandler = LLMHandler()
        self._tts: TTSHandler = TTSHandler()
        self._stt: STTHandler = STTHandler()
        self._conversation: ConversationManager = ConversationManager()
        self._formatter: ResponseFormatter = ResponseFormatter()
        
        print("VoiceBox initialized successfully!")
        print(f"Session ID: {self._conversation.session_id}")
    
    def process_text_input(
        self,
        user_input: str,
        generate_audio: bool = True,
        play_audio: bool = True
    ) -> Tuple[str, Optional[Path]]:
        """
        Process text input through the pipeline: LLM -> Format -> TTS.
        
        Args:
            user_input: The user's text input.
            generate_audio: Whether to generate audio output.
            play_audio: Whether to play the generated audio.
        
        Returns:
            Tuple[str, Optional[Path]]: Response text and audio file path (if generated).
        """
        print(f"\nUser: {user_input}")
        
        # Start timing
        start_time: float = time.time()
        
        # Add user message to history
        self._conversation.add_user_message(user_input)
        
        # Get conversation history for context (last 10 messages)
        history = self._conversation.get_conversation_history(max_messages=10)
        
        # Generate LLM response
        raw_response: str = self._llm.generate_response(user_input, history)
        
        # Format response for speech
        formatted_response: str = self._formatter.format_full_response(raw_response)
        
        # Add assistant message to history
        self._conversation.add_assistant_message(formatted_response)
        
        # Calculate response time
        response_time: float = time.time() - start_time
        
        # Log the interaction
        self._conversation.log_interaction(
            user_query=user_input,
            model_response=formatted_response,
            response_time=response_time,
            status="success"
        )
        
        print(f"Assistant: {formatted_response}")
        print(f"Response time: {response_time:.2f}s")
        
        # Generate audio if requested
        audio_path: Optional[Path] = None
        if generate_audio:
            timestamp: str = time.strftime("%Y%m%d_%H%M%S")
            filename: str = f"response_{timestamp}.wav"
            audio_path = self._tts.generate_and_save(formatted_response, filename)
            
            # Play audio if requested and generation was successful
            if play_audio and audio_path and audio_path.exists():
                self._play_audio(audio_path)
                # Delete the audio file after playing
                try:
                    audio_path.unlink()
                    audio_path = None  # Set to None since file is deleted
                except Exception as e:
                    print(f"Warning: Could not delete audio file: {e}")
        
        return formatted_response, audio_path
    
    def process_audio_input(
        self,
        audio_file_path: Path,
        generate_audio: bool = True
    ) -> Tuple[Optional[str], Optional[str], Optional[Path]]:
        """
        Process audio input through the full pipeline: STT -> LLM -> Format -> TTS.
        
        Args:
            audio_file_path: Path to the audio file containing user's speech.
            generate_audio: Whether to generate audio output.
        
        Returns:
            Tuple[Optional[str], Optional[str], Optional[Path]]: 
                Transcribed text, response text, and audio file path (if generated).
        """
        print(f"\nProcessing audio file: {audio_file_path}")
        
        # Transcribe audio to text
        transcribed_text, stt_info = self._stt.transcribe_audio(audio_file_path)
        
        if transcribed_text is None:
            print("Failed to transcribe audio")
            return None, None, None
        
        print(f"Transcribed: {transcribed_text}")
        
        # Process the transcribed text
        response_text, audio_path = self.process_text_input(
            transcribed_text,
            generate_audio=generate_audio,
            play_audio=True  # Always play audio in voice mode
        )
        
        return transcribed_text, response_text, audio_path
    
    def _play_audio(self, audio_path: Path) -> None:
        """
        Play audio file using system audio player.
        
        Args:
            audio_path: Path to the audio file to play.
        """
        try:
            # Try different audio players based on availability
            players = ['aplay', 'ffplay', 'mpg123', 'sox']
            
            for player in players:
                try:
                    if player == 'ffplay':
                        # ffplay with auto-exit and no video
                        subprocess.run(
                            ['ffplay', '-nodisp', '-autoexit', str(audio_path)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=True
                        )
                    elif player == 'aplay':
                        # aplay (ALSA player for Linux)
                        subprocess.run(
                            ['aplay', str(audio_path)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=True
                        )
                    else:
                        # Generic player
                        subprocess.run(
                            [player, str(audio_path)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=True
                        )
                    return  # Success, exit
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue  # Try next player
            
            print(f"Warning: No audio player found. Audio saved to: {audio_path}")
            
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def _record_audio(self, duration: int = 6) -> Optional[Path]:
        """
        Record audio from microphone using available recording tools.
        
        Args:
            duration: Recording duration in seconds (default: 5).
        
        Returns:
            Optional[Path]: Path to recorded audio file, or None if failed.
        """
        try:
            # Create temporary file for recording
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.wav',
                delete=False,
                dir=Config.AUDIO_DIR
            )
            temp_path = Path(temp_file.name)
            temp_file.close()
            
            print(f" Recording for {duration} seconds... Speak now!")
            
            # Try different recording methods
            recorders = [
                # arecord (ALSA recorder for Linux)
                ['arecord', '-d', str(duration), '-f', 'cd', str(temp_path)],
                # ffmpeg
                ['ffmpeg', '-f', 'alsa', '-i', 'default', '-t', str(duration), '-y', str(temp_path)],
                # sox
                ['rec', '-r', '16000', '-c', '1', str(temp_path), 'trim', '0', str(duration)]
            ]
            
            for cmd in recorders:
                try:
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True
                    )
                    
                    if temp_path.exists() and temp_path.stat().st_size > 0:
                        print("✓ Recording complete!")
                        return temp_path
                        
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue
            
            print("Error: No recording tool found (arecord, ffmpeg, or sox required)")
            if temp_path.exists():
                temp_path.unlink()
            return None
            
        except Exception as e:
            print(f"Error recording audio: {e}")
            return None
    
    def run_voice_interactive_mode(self, recording_duration: int = 5) -> None:
        """
        Run interactive voice conversation mode.
        User speaks input (via STT), receives spoken responses (via TTS).
        
        Args:
            recording_duration: Duration for each voice recording in seconds.
        """
        print("\n" + "="*60)
        print("VoiceBox Voice Interactive Mode")
        print("Press ENTER to start recording, speak your message")
        print("Commands: 'quit', 'exit', or 'q' to stop, 'stats' for statistics")
        print("         'text' to switch to text mode")
        print(f"Recording duration: {recording_duration} seconds")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("Press ENTER to speak (or type command): ").strip().lower()
                
                # Check for commands
                if user_input in ['quit', 'exit', 'q']:
                    print("\nEnding conversation...")
                    break
                
                if user_input == 'stats':
                    stats = self._conversation.get_statistics()
                    print("\nConversation Statistics:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                    continue
                
                if user_input == 'text':
                    print("\nSwitching to text mode...")
                    self.run_interactive_text_mode()
                    return
                
                # Record audio
                audio_path = self._record_audio(duration=recording_duration)
                
                if audio_path is None:
                    print("Failed to record audio. Please try again.")
                    continue
                
                # Process the audio
                transcribed_text, response_text, response_audio = self.process_audio_input(
                    audio_path,
                    generate_audio=True
                )
                
                # Clean up temporary recording
                if audio_path.exists():
                    audio_path.unlink()
                
                if transcribed_text is None:
                    print("Failed to transcribe. Please try again.")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        # Save conversation before exiting
        self._save_and_exit()
    
    def run_interactive_text_mode(self) -> None:
        """
        Run interactive text-based conversation mode.
        User types input, receives text and audio responses.
        """
        print("\n" + "="*60)
        print("VoiceBox Interactive Text Mode")
        print("Type your messages and press Enter")
        print("Commands: 'quit' or 'exit' to stop, 'stats' for statistics")
        print("         'voice' to switch to voice mode")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input: str = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nEnding conversation...")
                    break
                
                if user_input.lower() == 'stats':
                    stats = self._conversation.get_statistics()
                    print("\nConversation Statistics:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                    continue
                
                if user_input.lower() == 'voice':
                    print("\nSwitching to voice mode...")
                    self.run_voice_interactive_mode()
                    return
                
                # Process input with audio playback
                self.process_text_input(user_input, generate_audio=True, play_audio=True)
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        # Save conversation before exiting
        self._save_and_exit()
    
    def run_hybrid_mode(self) -> None:
        """
        Run hybrid mode where user can choose between text or voice input each turn.
        Responses are always spoken.
        """
        print("\n" + "="*60)
        print("VoiceBox Hybrid Interactive Mode")
        print("Choose input method for each message:")
        print("  - Type 'v' or 'voice' then ENTER to speak")
        print("  - Type your message directly for text input")
        print("Commands: 'quit' or 'exit' to stop, 'stats' for statistics")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input: str = input("You (text/voice/command): ").strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nEnding conversation...")
                    break
                
                if user_input.lower() == 'stats':
                    stats = self._conversation.get_statistics()
                    print("\nConversation Statistics:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                    continue
                
                # Voice input
                if user_input.lower() in ['v', 'voice']:
                    audio_path = self._record_audio(duration=5)
                    
                    if audio_path is None:
                        print("Failed to record audio. Please try again.")
                        continue
                    
                    # Process the audio
                    transcribed_text, response_text, response_audio = self.process_audio_input(
                        audio_path,
                        generate_audio=True
                    )
                    
                    # Clean up temporary recording
                    if audio_path.exists():
                        audio_path.unlink()
                    
                    if transcribed_text is None:
                        print("Failed to transcribe. Please try again.")
                else:
                    # Text input
                    self.process_text_input(user_input, generate_audio=True, play_audio=True)
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        # Save conversation before exiting
        self._save_and_exit()
    
    def _save_and_exit(self) -> None:
        """
        Save conversation and display statistics before exiting.
        """
        print("\n" + "="*60)
        
        # Show statistics
        stats = self._conversation.get_statistics()
        print("Session Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Save conversation
        saved_path: Path = self._conversation.save_conversation()
        print(f"\nConversation saved to: {saved_path}")
        print("Thank you for using VoiceBox!")
        print("="*60)
    
    @property
    def session_id(self) -> str:
        """
        Get the current session ID.
        
        Returns:
            str: The session ID.
        """
        return self._conversation.session_id


def main() -> None:
    """
    Main entry point for VoiceBox application.
    """
    try:
        # Create controller
        controller: VoiceBoxController = VoiceBoxController()
        
        # Ask user for mode preference
        print("\nSelect interaction mode:")
        print("  1. Text Mode - Type your messages (responses will be spoken)")
        print("  2. Voice Mode - Speak your messages (responses will be spoken)")
        print("  3. Hybrid Mode - Choose text or voice for each message")
        
        while True:
            mode = input("\nEnter mode (1/2/3) [default: 3]: ").strip()
            
            if not mode or mode == '3':
                controller.run_hybrid_mode()
                break
            elif mode == '1':
                controller.run_interactive_text_mode()
                break
            elif mode == '2':
                controller.run_voice_interactive_mode()
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
