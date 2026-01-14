"""
VoiceBox Main Controller.
Orchestrates all components: LLM, TTS, STT, conversation management,
wake word detection, search, and audio interruption.

Feature Toggles:
    ENABLE_LLM: Enable/disable LLM for response generation
    ENABLE_STT: Enable/disable Speech-to-Text
    ENABLE_TTS: Enable/disable Text-to-Speech
    ENABLE_RAG: Enable/disable RAG (Retrieval Augmented Generation)
    ENABLE_SEARCH: Enable/disable real-time web search
    ENABLE_WAKEWORD: Enable/disable wake word detection
    ENABLE_INTERRUPT: Enable/disable TTS interruption via keypress/wake word
"""

import sys
from pathlib import Path
from typing import Optional, Tuple
import time
import subprocess
import tempfile
import os
import threading

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config.config import Config
from config.logger import get_logger, suppress_library_warnings

# Suppress third-party library warnings
suppress_library_warnings()

logger = get_logger('main')


# ============================================================================
# FEATURE TOGGLES - Set these to True/False to enable/disable features
# ============================================================================
ENABLE_LLM: bool = True           # LLM response generation
ENABLE_STT: bool = True           # Speech-to-Text transcription
ENABLE_TTS: bool = True           # Text-to-Speech audio output
ENABLE_RAG: bool = True           # RAG context retrieval
ENABLE_SEARCH: bool = True        # Real-time web search (Tavily)
ENABLE_WAKEWORD: bool = True      # Wake word detection (Porcupine)
ENABLE_INTERRUPT: bool = True     # Allow interrupting TTS with keypress/wake word
# ============================================================================


class VoiceBoxController:
    """
    Central controller that orchestrates all VoiceBox components.
    Manages the flow between STT, LLM, TTS, wake word, search, and conversation logging.
    Supports feature toggles for testing different module combinations.
    """
    
    def __init__(
        self,
        enable_llm: bool = ENABLE_LLM,
        enable_stt: bool = ENABLE_STT,
        enable_tts: bool = ENABLE_TTS,
        enable_rag: bool = ENABLE_RAG,
        enable_search: bool = ENABLE_SEARCH,
        enable_wakeword: bool = ENABLE_WAKEWORD,
        enable_interrupt: bool = ENABLE_INTERRUPT
    ) -> None:
        """
        Initialize the VoiceBox controller with configurable features.
        
        Args:
            enable_llm: Enable LLM response generation.
            enable_stt: Enable Speech-to-Text.
            enable_tts: Enable Text-to-Speech.
            enable_rag: Enable RAG context retrieval.
            enable_search: Enable real-time web search.
            enable_wakeword: Enable wake word detection.
            enable_interrupt: Enable TTS interruption.
        """
        # Store feature flags
        self._enable_llm = enable_llm
        self._enable_stt = enable_stt
        self._enable_tts = enable_tts
        self._enable_rag = enable_rag
        self._enable_search = enable_search
        self._enable_wakeword = enable_wakeword
        self._enable_interrupt = enable_interrupt
        
        logger.info("Initializing VoiceBox...")
        logger.info(f"Feature flags: LLM={enable_llm}, STT={enable_stt}, TTS={enable_tts}, "
                   f"RAG={enable_rag}, Search={enable_search}, WakeWord={enable_wakeword}, "
                   f"Interrupt={enable_interrupt}")
        print("Initializing VoiceBox...")
        
        # Ensure directories exist
        Config.ensure_directories()
        logger.info("Directories ensured")
        
        # Initialize components based on feature flags
        self._llm = None
        self._tts = None
        self._stt = None
        self._wakeword = None
        self._audio_controller = None
        self._conversation = None
        self._formatter = None
        
        try:
            # Initialize LLM handler
            if self._enable_llm:
                logger.info("Initializing LLM handler...")
                from modules.llm_handler import LLMHandler
                self._llm = LLMHandler()
                # Configure RAG and Search based on flags
                self._llm.set_rag_enabled(self._enable_rag)
                self._llm.set_search_enabled(self._enable_search)
                logger.info("LLM handler initialized")
            
            # Initialize TTS handler
            if self._enable_tts:
                logger.info("Initializing TTS handler...")
                from modules.tts_handler import TTSHandler
                self._tts = TTSHandler()
                logger.info("TTS handler initialized")
            
            # Initialize STT handler
            if self._enable_stt:
                logger.info("Initializing STT handler...")
                from modules.stt_handler import STTHandler
                self._stt = STTHandler()
                logger.info("STT handler initialized")
            
            # Initialize wake word handler
            if self._enable_wakeword:
                logger.info("Initializing wake word handler...")
                try:
                    from modules.wakeword_handler import WakeWordHandler
                    self._wakeword = WakeWordHandler()
                    if self._wakeword.is_enabled:
                        logger.info("Wake word handler initialized")
                    else:
                        logger.warning("Wake word handler disabled (check API key)")
                except ImportError as e:
                    logger.warning(f"Wake word handler not available: {e}")
                    self._wakeword = None
            
            # Initialize audio controller for interruptible playback
            if self._enable_interrupt and self._enable_tts:
                logger.info("Initializing audio controller...")
                try:
                    from modules.audio_controller import AudioController
                    self._audio_controller = AudioController()
                    if self._wakeword:
                        self._audio_controller.set_wakeword_handler(self._wakeword)
                    logger.info("Audio controller initialized")
                except ImportError as e:
                    logger.warning(f"Audio controller not available: {e}")
                    self._audio_controller = None
            
            # Initialize conversation manager
            logger.info("Initializing conversation manager...")
            from modules.conversation_manager import ConversationManager
            self._conversation = ConversationManager()
            logger.info("Conversation manager initialized")
            
            # Initialize response formatter
            logger.info("Initializing response formatter...")
            from modules.response_formatter import ResponseFormatter
            self._formatter = ResponseFormatter()
            logger.info("Response formatter initialized")
            
            logger.info("VoiceBox initialized successfully!")
            print("VoiceBox initialized successfully!")
            print(f"Session ID: {self._conversation.session_id}")
            self._print_feature_status()
            logger.info(f"Session ID: {self._conversation.session_id}")
            
        except Exception as e:
            logger.error("Failed to initialize VoiceBox", exc_info=True)
            print(f"Initialization error: {e}")
            raise
    
    def _print_feature_status(self) -> None:
        """Print the status of all features."""
        print("\nFeature Status:")
        print(f"  LLM:        {'✓ Enabled' if self._enable_llm and self._llm else '✗ Disabled'}")
        print(f"  STT:        {'✓ Enabled' if self._enable_stt and self._stt else '✗ Disabled'}")
        print(f"  TTS:        {'✓ Enabled' if self._enable_tts and self._tts else '✗ Disabled'}")
        print(f"  RAG:        {'✓ Enabled' if self._enable_rag and self._llm and self._llm.rag_enabled else '✗ Disabled'}")
        print(f"  Search:     {'✓ Enabled' if self._enable_search and self._llm and self._llm.search_enabled else '✗ Disabled'}")
        print(f"  Wake Word:  {'✓ Enabled' if self._enable_wakeword and self._wakeword and self._wakeword.is_enabled else '✗ Disabled'}")
        print(f"  Interrupt:  {'✓ Enabled' if self._enable_interrupt and self._audio_controller else '✗ Disabled'}")
    
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
        logger.info(f"Processing text input: {user_input}")
        print(f"\nUser: {user_input}")
        
        # Start timing
        start_time: float = time.time()
        
        try:
            # Add user message to history
            logger.debug("Adding user message to history")
            self._conversation.add_user_message(user_input)
            
            # Get conversation history for context (last 10 messages)
            logger.debug("Retrieving conversation history")
            history = self._conversation.get_conversation_history(max_messages=10)
            
            # Generate LLM response (if enabled)
            if self._llm:
                logger.info("Generating LLM response")
                result = self._llm.generate_response(user_input, history)
                
                # Handle both old format (string) and new format (tuple with attributions)
                if isinstance(result, tuple):
                    raw_response, attributions = result
                else:
                    raw_response = result
                    attributions = []
            else:
                raw_response = f"[LLM disabled] Echo: {user_input}"
                attributions = []
            
            logger.debug(f"Raw response: {raw_response[:100]}...")
            
            # Format response for speech
            logger.debug("Formatting response for speech")
            formatted_response: str = self._formatter.format_full_response(raw_response)
            logger.debug(f"Formatted response: {formatted_response[:100]}...")
            
            # Add assistant message to history
            logger.debug("Adding assistant message to history")
            self._conversation.add_assistant_message(formatted_response)
            
            # Calculate response time
            response_time: float = time.time() - start_time
            logger.info(f"Response generation time: {response_time:.2f}s")
            
            # Log the interaction
            logger.debug("Logging interaction to conversation file")
            self._conversation.log_interaction(
                user_query=user_input,
                model_response=formatted_response,
                response_time=response_time,
                status="success"
            )
            
            print(f"Assistant: {formatted_response}")
            print(f"Response time: {response_time:.2f}s")
            
            # Print source attributions if available
            if attributions and self._llm:
                attribution_text = self._llm.get_source_attribution_text(attributions)
                if attribution_text:
                    print(f"\n{attribution_text}")
                    logger.info(f"Sources: {[a.get('section', a.get('title', 'Unknown')) for a in attributions]}")
            
            # Generate audio if requested and TTS is enabled
            audio_path: Optional[Path] = None
            interrupted: bool = False
            
            if generate_audio and self._tts and self._enable_tts:
                logger.info("Generating audio from response")
                timestamp: str = time.strftime("%Y%m%d_%H%M%S")
                filename: str = f"response_{timestamp}.wav"
                audio_path = self._tts.generate_and_save(formatted_response, filename)
                logger.info(f"Audio generated: {audio_path}")
                
                # Play audio if requested and generation was successful
                if play_audio and audio_path and audio_path.exists():
                    logger.info("Playing audio")
                    interrupted = self._play_audio_with_interrupt(audio_path)
                    
                    # Delete the audio file after playing
                    try:
                        audio_path.unlink()
                        logger.debug("Audio file deleted after playback")
                        audio_path = None  # Set to None since file is deleted
                    except Exception as e:
                        logger.warning(f"Could not delete audio file: {e}")
                        print(f"Warning: Could not delete audio file: {e}")
            
            return formatted_response, audio_path
            
        except Exception as e:
            logger.error("Error processing text input", exc_info=True)
            print(f"Error: {e}")
            raise
    
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
        if not self._stt or not self._enable_stt:
            logger.warning("STT is disabled")
            print("STT is disabled")
            return None, None, None
        
        logger.info(f"Processing audio file: {audio_file_path}")
        print(f"\nProcessing audio file: {audio_file_path}")
        
        try:
            # Transcribe audio to text
            logger.info("Transcribing audio to text")
            transcribed_text, stt_info = self._stt.transcribe_audio(audio_file_path)
            logger.debug(f"STT info: {stt_info}")
            
            if transcribed_text is None:
                logger.error("Failed to transcribe audio")
                print("Failed to transcribe audio")
                return None, None, None
            
            logger.info(f"Transcribed text: {transcribed_text}")
            print(f"Transcribed: {transcribed_text}")
            
            # Process the transcribed text
            logger.info("Processing transcribed text through LLM and TTS")
            response_text, audio_path = self.process_text_input(
                transcribed_text,
                generate_audio=generate_audio,
                play_audio=True  # Always play audio in voice mode
            )
            logger.info("Audio processing complete")
            
            return transcribed_text, response_text, audio_path
            
        except Exception as e:
            logger.error("Error processing audio input", exc_info=True)
            print(f"Error: {e}")
            return None, None, None
    
    def _play_audio_with_interrupt(self, audio_path: Path) -> bool:
        """
        Play audio file with interrupt support (keypress or wake word).
        
        Args:
            audio_path: Path to the audio file to play.
        
        Returns:
            bool: True if playback was interrupted, False if completed.
        """
        if self._audio_controller and self._enable_interrupt:
            # Use audio controller for interruptible playback
            completed, reason = self._audio_controller.play_audio_interruptible(
                audio_path,
                allow_keypress=True,
                allow_wakeword=self._enable_wakeword and self._wakeword is not None
            )
            
            if not completed:
                logger.info(f"Playback interrupted by: {reason}")
                print(f"\n[Interrupted by {reason}]")
                return True
            return False
        else:
            # Fall back to simple playback
            self._play_audio(audio_path)
            return False
    
    def _play_audio(self, audio_path: Path) -> None:
        """
        Play audio file using system audio player (non-interruptible).
        
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
            
            logger.warning("No audio player found")
            print(f"Warning: No audio player found. Audio saved to: {audio_path}")
            
        except Exception as e:
            logger.error("Error playing audio", exc_info=True)
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
            logger.info(f"Starting audio recording for {duration} seconds")
            # Create temporary file for recording
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.wav',
                delete=False,
                dir=Config.AUDIO_DIR
            )
            temp_path = Path(temp_file.name)
            temp_file.close()
            logger.debug(f"Recording to temporary file: {temp_path}")
            
            print(f"[Recording] Recording for {duration} seconds... Speak now!")
            
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
                    logger.debug(f"Trying recorder: {cmd[0]}")
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True
                    )
                    
                    if temp_path.exists() and temp_path.stat().st_size > 0:
                        logger.info(f"Recording complete: {temp_path.stat().st_size} bytes")
                        print("✓ Recording complete!")
                        return temp_path
                        
                except (FileNotFoundError, subprocess.CalledProcessError) as e:
                    logger.debug(f"Recorder {cmd[0]} failed: {e}")
                    continue
            
            logger.error("No recording tool found")
            print("Error: No recording tool found (arecord, ffmpeg, or sox required)")
            if temp_path.exists():
                temp_path.unlink()
            return None
            
        except Exception as e:
            logger.error("Error recording audio", exc_info=True)
            print(f"Error recording audio: {e}")
            return None
    
    def run_voice_interactive_mode(self, recording_duration: int = 6) -> None:
        """
        Run interactive voice conversation mode.
        User speaks input (via STT), receives spoken responses (via TTS).
        Supports wake word activation and TTS interruption.
        
        Args:
            recording_duration: Duration for each voice recording in seconds.
        """
        if not self._stt or not self._enable_stt:
            print("\nVoice mode requires STT to be enabled.")
            print("Falling back to text mode...")
            self.run_interactive_text_mode()
            return
        
        logger.info(f"Starting voice interactive mode (duration={recording_duration}s)")
        print("\n" + "="*60)
        print("VoiceBox Voice Interactive Mode")
        print("Press ENTER to start recording, speak your message")
        if self._wakeword and self._wakeword.is_enabled:
            print("Or say the wake word at any time to activate")
        print("Commands: 'quit', 'exit', or 'q' to stop, 'stats' for statistics")
        print("         'text' to switch to text mode")
        if self._enable_interrupt:
            print("During speech: Press 's' or say wake word to interrupt")
        print(f"Recording duration: {recording_duration} seconds")
        print("="*60 + "\n")
        
        # Start wake word listening in background if available
        if self._wakeword and self._wakeword.is_enabled and self._enable_wakeword:
            self._wakeword.start_listening()
            logger.info("Wake word listening started")
        
        try:
            while True:
                try:
                    # Check if wake word was detected
                    if self._wakeword and self._wakeword.is_detected:
                        print("\n🎤 Wake word detected! Recording...")
                        audio_path = self._record_audio(duration=recording_duration)
                        if audio_path:
                            self._process_voice_input(audio_path)
                        continue
                    
                    user_input = input("Press ENTER to speak (or type command): ").strip().lower()
                    
                    # Check for commands
                    if user_input in ['quit', 'exit', 'q']:
                        logger.info("User requested exit from voice mode")
                        print("\nEnding conversation...")
                        break
                    
                    if user_input == 'stats':
                        logger.debug("User requested statistics")
                        stats = self._conversation.get_statistics()
                        print("\nConversation Statistics:")
                        for key, value in stats.items():
                            print(f"  {key}: {value}")
                        self._print_feature_status()
                        continue
                    
                    if user_input == 'text':
                        logger.info("Switching to text mode")
                        print("\nSwitching to text mode...")
                        self.run_interactive_text_mode()
                        return
                    
                    if user_input == 'features':
                        self._print_feature_status()
                        continue
                    
                    # Record audio
                    logger.info("Starting voice recording")
                    audio_path = self._record_audio(duration=recording_duration)
                    
                    if audio_path is None:
                        logger.warning("Audio recording failed")
                        print("Failed to record audio. Please try again.")
                        continue
                    
                    # Process the audio
                    self._process_voice_input(audio_path)
                    
                except KeyboardInterrupt:
                    logger.info("Voice mode interrupted by user (Ctrl+C)")
                    print("\n\nInterrupted by user")
                    break
                except Exception as e:
                    logger.error("Error in voice interactive mode", exc_info=True)
                    print(f"Error: {e}")
        finally:
            # Stop wake word listening
            if self._wakeword and self._wakeword.is_listening:
                self._wakeword.stop_listening()
                logger.info("Wake word listening stopped")
        
        # Save conversation before exiting
        logger.info("Exiting voice mode")
        self._save_and_exit()
    
    def _process_voice_input(self, audio_path: Path) -> None:
        """
        Process recorded voice input through the pipeline.
        
        Args:
            audio_path: Path to the recorded audio file.
        """
        logger.info("Processing recorded audio")
        transcribed_text, response_text, response_audio = self.process_audio_input(
            audio_path,
            generate_audio=self._enable_tts
        )
        
        # Clean up temporary recording
        if audio_path.exists():
            logger.debug("Cleaning up temporary recording")
            audio_path.unlink()
        
        if transcribed_text is None:
            logger.warning("Transcription failed")
            print("Failed to transcribe. Please try again.")
    
    def run_interactive_text_mode(self) -> None:
        """
        Run interactive text-based conversation mode.
        User types input, receives text and audio responses.
        Supports TTS interruption with keypress.
        """
        logger.info("Starting text interactive mode")
        print("\n" + "="*60)
        print("VoiceBox Interactive Text Mode")
        print("Type your messages and press Enter")
        print("Commands: 'quit' or 'exit' to stop, 'stats' for statistics")
        print("         'voice' to switch to voice mode, 'features' for status")
        if self._enable_interrupt and self._enable_tts:
            print("During speech: Press 's' to skip/interrupt")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input: str = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    logger.info("User requested exit from text mode")
                    print("\nEnding conversation...")
                    break
                
                if user_input.lower() == 'stats':
                    logger.debug("User requested statistics")
                    stats = self._conversation.get_statistics()
                    print("\nConversation Statistics:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                    continue
                
                if user_input.lower() == 'features':
                    self._print_feature_status()
                    continue
                
                if user_input.lower() == 'voice':
                    if self._enable_stt and self._stt:
                        logger.info("Switching to voice mode")
                        print("\nSwitching to voice mode...")
                        self.run_voice_interactive_mode()
                        return
                    else:
                        print("Voice mode requires STT to be enabled.")
                        continue
                
                # Process input with audio playback
                logger.info(f"Processing text input: {user_input[:50]}...")
                self.process_text_input(
                    user_input,
                    generate_audio=self._enable_tts,
                    play_audio=self._enable_tts
                )
                
            except KeyboardInterrupt:
                logger.info("Text mode interrupted by user (Ctrl+C)")
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                logger.error("Error in text interactive mode", exc_info=True)
                print(f"Error: {e}")
        
        # Save conversation before exiting
        logger.info("Exiting text mode")
        self._save_and_exit()
    
    def _save_and_exit(self) -> None:
        """
        Save conversation and display statistics before exiting.
        """
        logger.info("Saving conversation and exiting")
        print("\n" + "="*60)
        
        # Show statistics
        stats = self._conversation.get_statistics()
        logger.info(f"Session statistics: {stats}")
        print("Session Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Save conversation
        saved_path: Path = self._conversation.save_conversation()
        logger.info(f"Conversation saved to: {saved_path}")
        print(f"\nConversation saved to: {saved_path}")
        print("Thank you for using VoiceBox!")
        print("="*60)
    
    def cleanup(self) -> None:
        """Clean up all resources."""
        if self._wakeword:
            self._wakeword.cleanup()
        if self._audio_controller:
            self._audio_controller.cleanup()
        logger.info("VoiceBox controller cleaned up")
    
    @property
    def session_id(self) -> str:
        """
        Get the current session ID.
        
        Returns:
            str: The session ID.
        """
        return self._conversation.session_id


def print_feature_menu() -> None:
    """Print the feature configuration menu."""
    print("\n" + "="*60)
    print("VoiceBox Feature Configuration")
    print("="*60)
    print("\nCurrent global settings (edit in main.py to change defaults):")
    print(f"  ENABLE_LLM:       {ENABLE_LLM}")
    print(f"  ENABLE_STT:       {ENABLE_STT}")
    print(f"  ENABLE_TTS:       {ENABLE_TTS}")
    print(f"  ENABLE_RAG:       {ENABLE_RAG}")
    print(f"  ENABLE_SEARCH:    {ENABLE_SEARCH}")
    print(f"  ENABLE_WAKEWORD:  {ENABLE_WAKEWORD}")
    print(f"  ENABLE_INTERRUPT: {ENABLE_INTERRUPT}")
    print("="*60)


def main() -> None:
    """
    Main entry point for VoiceBox application.
    Supports feature toggle configuration via global variables.
    """
    try:
        logger.info("="*60)
        logger.info("VoiceBox application starting")
        logger.info("="*60)
        
        # Print feature configuration
        print_feature_menu()
        
        # Create controller with global feature settings
        logger.info("Creating VoiceBox controller")
        controller: VoiceBoxController = VoiceBoxController(
            enable_llm=ENABLE_LLM,
            enable_stt=ENABLE_STT,
            enable_tts=ENABLE_TTS,
            enable_rag=ENABLE_RAG,
            enable_search=ENABLE_SEARCH,
            enable_wakeword=ENABLE_WAKEWORD,
            enable_interrupt=ENABLE_INTERRUPT
        )
        
        # Ask user for mode preference
        print("\nSelect interaction mode:")
        print("  1. Text Mode - Type your messages")
        if ENABLE_STT:
            print("  2. Voice Mode - Speak your messages")
        
        while True:
            mode = input("\nEnter mode (1/2) [default: 1]: ").strip()
            
            if not mode or mode == '1':
                logger.info("User selected text mode")
                controller.run_interactive_text_mode()
                break
            elif mode == '2' and ENABLE_STT:
                logger.info("User selected voice mode")
                controller.run_voice_interactive_mode()
                break
            elif mode == '2' and not ENABLE_STT:
                print("Voice mode requires STT to be enabled (ENABLE_STT=True)")
            else:
                logger.debug(f"Invalid mode selection: {mode}")
                print("Invalid choice. Please enter 1 or 2.")
        
        # Cleanup
        controller.cleanup()
        logger.info("VoiceBox application ended normally")
        
    except Exception as e:
        logger.error("Fatal error in main", exc_info=True)
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
