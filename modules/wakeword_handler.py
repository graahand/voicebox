"""
Wake Word Handler module for VoiceBox project.
Provides wake word detection using Picovoice Porcupine.
Supports continuous listening for wake word during TTS playback.
"""

import os
import struct
import threading
import time
from typing import Optional, Callable, List
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config
from config.logger import get_logger, suppress_library_warnings

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Config.BASE_DIR / ".env")
except ImportError:
    pass

suppress_library_warnings()

logger = get_logger('wakeword')


class WakeWordHandler:
    """
    Singleton class for handling wake word detection using Picovoice Porcupine.
    Runs in a separate thread to allow continuous monitoring.
    """
    
    _instance: Optional['WakeWordHandler'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'WakeWordHandler':
        """
        Implement singleton pattern with thread safety.
        
        Returns:
            WakeWordHandler: The singleton instance.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self) -> None:
        """
        Initialize wake word handler.
        Only runs once due to singleton pattern.
        """
        if self._initialized:
            return
        
        self._access_key: Optional[str] = os.getenv('PICOVOICE_ACCESS_KEY')
        self._porcupine = None
        self._audio_stream = None
        self._pa = None
        self._enabled: bool = False
        self._listening: bool = False
        self._detected: bool = False
        self._listen_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._callbacks: List[Callable[[], None]] = []
        self._initialized = True
        
        # Wake word model path
        self._keyword_path: Optional[Path] = None
        self._find_keyword_model()
        
        # Initialize Porcupine
        self._init_porcupine()
    
    def _find_keyword_model(self) -> None:
        """
        Find the wake word model file.
        """
        # Look for .ppn files in the data directory
        model_patterns = [
            Config.DATA_DIR / "vision_en_raspberry-pi_v4_0_0" / "vision_en_raspberry-pi_v4_0_0.ppn",
            Config.DATA_DIR / "*.ppn",
        ]
        
        for pattern in model_patterns:
            if pattern.exists():
                self._keyword_path = pattern
                logger.info(f"Found wake word model: {pattern}")
                return
        
        # Search recursively
        ppn_files = list(Config.DATA_DIR.rglob("*.ppn"))
        if ppn_files:
            self._keyword_path = ppn_files[0]
            logger.info(f"Found wake word model: {self._keyword_path}")
        else:
            logger.warning("No wake word model (.ppn) found in data directory")
    
    def _init_porcupine(self) -> None:
        """
        Initialize the Porcupine wake word engine.
        """
        if not self._access_key or self._access_key == 'your_picovoice_access_key_here':
            logger.warning("Picovoice access key not configured. Wake word disabled.")
            logger.info("Set PICOVOICE_ACCESS_KEY in .env file to enable wake word.")
            self._enabled = False
            return
        
        if not self._keyword_path or not self._keyword_path.exists():
            logger.warning("Wake word model not found. Wake word disabled.")
            self._enabled = False
            return
        
        try:
            import pvporcupine
            
            logger.info(f"Initializing Porcupine with keyword: {self._keyword_path.name}")
            
            # Create Porcupine instance with custom keyword
            self._porcupine = pvporcupine.create(
                access_key=self._access_key,
                keyword_paths=[str(self._keyword_path)]
            )
            
            self._enabled = True
            logger.info("Porcupine wake word engine initialized successfully")
            logger.info(f"Sample rate: {self._porcupine.sample_rate}")
            logger.info(f"Frame length: {self._porcupine.frame_length}")
            
        except ImportError as e:
            logger.warning(f"pvporcupine not installed: {e}")
            logger.info("Install with: pip install pvporcupine")
            self._enabled = False
        except Exception as e:
            logger.error(f"Error initializing Porcupine: {e}", exc_info=True)
            self._enabled = False
    
    def _init_audio_stream(self) -> bool:
        """
        Initialize the audio input stream for wake word detection.
        
        Returns:
            bool: True if successful.
        """
        if not self._porcupine:
            return False
        
        try:
            import pyaudio
            
            self._pa = pyaudio.PyAudio()
            self._audio_stream = self._pa.open(
                rate=self._porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self._porcupine.frame_length
            )
            
            logger.debug("Audio stream initialized for wake word detection")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing audio stream: {e}", exc_info=True)
            return False
    
    def _close_audio_stream(self) -> None:
        """
        Close the audio input stream.
        """
        if self._audio_stream:
            try:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
            except Exception as e:
                logger.debug(f"Error closing audio stream: {e}")
            self._audio_stream = None
        
        if self._pa:
            try:
                self._pa.terminate()
            except Exception as e:
                logger.debug(f"Error terminating PyAudio: {e}")
            self._pa = None
    
    def _listen_loop(self) -> None:
        """
        Main listening loop for wake word detection.
        Runs in a separate thread.
        """
        if not self._init_audio_stream():
            logger.error("Failed to initialize audio stream for wake word")
            return
        
        logger.info("Wake word listening started")
        self._listening = True
        
        try:
            while not self._stop_event.is_set():
                try:
                    # Read audio frame
                    pcm = self._audio_stream.read(
                        self._porcupine.frame_length,
                        exception_on_overflow=False
                    )
                    pcm = struct.unpack_from("h" * self._porcupine.frame_length, pcm)
                    
                    # Process with Porcupine
                    keyword_index = self._porcupine.process(pcm)
                    
                    if keyword_index >= 0:
                        logger.info("Wake word detected!")
                        self._detected = True
                        
                        # Call registered callbacks
                        for callback in self._callbacks:
                            try:
                                callback()
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
                        
                        # Brief pause after detection
                        time.sleep(0.5)
                        self._detected = False
                        
                except Exception as e:
                    if not self._stop_event.is_set():
                        logger.debug(f"Audio read error: {e}")
                    time.sleep(0.01)
                    
        finally:
            self._listening = False
            self._close_audio_stream()
            logger.info("Wake word listening stopped")
    
    def start_listening(self) -> bool:
        """
        Start wake word detection in background thread.
        
        Returns:
            bool: True if started successfully.
        """
        if not self._enabled:
            logger.warning("Wake word not enabled")
            return False
        
        if self._listening:
            logger.debug("Wake word already listening")
            return True
        
        self._stop_event.clear()
        self._listen_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="WakeWordListener"
        )
        self._listen_thread.start()
        
        # Wait for thread to start
        time.sleep(0.1)
        return self._listening
    
    def stop_listening(self) -> None:
        """
        Stop wake word detection.
        """
        if not self._listening:
            return
        
        logger.info("Stopping wake word detection...")
        self._stop_event.set()
        
        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=2.0)
        
        self._listen_thread = None
    
    def register_callback(self, callback: Callable[[], None]) -> None:
        """
        Register a callback to be called when wake word is detected.
        
        Args:
            callback: Function to call on wake word detection.
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            logger.debug(f"Registered wake word callback: {callback.__name__}")
    
    def unregister_callback(self, callback: Callable[[], None]) -> None:
        """
        Unregister a callback.
        
        Args:
            callback: Function to remove.
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def clear_callbacks(self) -> None:
        """Clear all registered callbacks."""
        self._callbacks.clear()
    
    def wait_for_wake_word(self, timeout: Optional[float] = None) -> bool:
        """
        Block until wake word is detected or timeout.
        
        Args:
            timeout: Maximum time to wait in seconds (None = forever).
        
        Returns:
            bool: True if wake word was detected.
        """
        if not self._enabled:
            return False
        
        was_listening = self._listening
        if not was_listening:
            self.start_listening()
        
        start_time = time.time()
        detected = False
        
        while True:
            if self._detected:
                detected = True
                break
            
            if timeout and (time.time() - start_time) >= timeout:
                break
            
            time.sleep(0.05)
        
        if not was_listening:
            self.stop_listening()
        
        return detected
    
    @property
    def is_detected(self) -> bool:
        """Check if wake word was just detected."""
        return self._detected
    
    @property
    def is_enabled(self) -> bool:
        """Check if wake word detection is enabled."""
        return self._enabled
    
    @property
    def is_listening(self) -> bool:
        """Check if currently listening for wake word."""
        return self._listening
    
    def cleanup(self) -> None:
        """
        Clean up resources.
        """
        self.stop_listening()
        self.clear_callbacks()
        
        if self._porcupine:
            try:
                self._porcupine.delete()
            except Exception as e:
                logger.debug(f"Error deleting Porcupine: {e}")
            self._porcupine = None
        
        self._enabled = False
        logger.info("Wake word handler cleaned up")
    
    def __del__(self):
        """Destructor to clean up resources."""
        self.cleanup()


def main() -> None:
    """
    Main function for testing wake word handler.
    """
    print("Testing Wake Word Handler")
    print("=" * 40)
    
    handler = WakeWordHandler()
    
    print(f"Enabled: {handler.is_enabled}")
    
    if handler.is_enabled:
        print("\nStarting wake word detection...")
        print("Say the wake word to trigger detection.")
        print("Press Ctrl+C to stop.\n")
        
        def on_wake_word():
            print("*** WAKE WORD DETECTED! ***")
        
        handler.register_callback(on_wake_word)
        handler.start_listening()
        
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping...")
        
        handler.stop_listening()
        handler.cleanup()
    else:
        print("\nWake word detection is disabled.")
        print("Check that:")
        print("  1. PICOVOICE_ACCESS_KEY is set in .env")
        print("  2. A .ppn wake word model exists in data/")
        print("  3. pvporcupine and pyaudio are installed")


if __name__ == '__main__':
    main()
