"""
Audio Controller module for VoiceBox project.
Handles interruptible audio playback and concurrent STT/TTS operations.
Provides thread-safe audio management with wake word and keypress interruption.
"""

import os
import sys
import time
import signal
import select
import subprocess
import threading
from typing import Optional, Callable, Tuple
from pathlib import Path
from queue import Queue, Empty

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config
from config.logger import get_logger, suppress_library_warnings

suppress_library_warnings()

logger = get_logger('audio_controller')


class KeyboardMonitor:
    """
    Non-blocking keyboard monitor for interrupt detection.
    Works on Linux/Unix systems.
    """
    
    def __init__(self):
        self._running = False
        self._key_queue: Queue = Queue()
        self._thread: Optional[threading.Thread] = None
        self._old_settings = None
    
    def _setup_terminal(self) -> bool:
        """Set up terminal for non-blocking input."""
        try:
            import termios
            import tty
            
            self._old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            return True
        except Exception as e:
            logger.debug(f"Could not set up terminal: {e}")
            return False
    
    def _restore_terminal(self) -> None:
        """Restore terminal settings."""
        try:
            import termios
            if self._old_settings:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)
        except Exception as e:
            logger.debug(f"Could not restore terminal: {e}")
    
    def _monitor_loop(self) -> None:
        """Monitor keyboard input in a loop."""
        while self._running:
            try:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    self._key_queue.put(char)
            except Exception:
                time.sleep(0.1)
    
    def start(self) -> bool:
        """Start keyboard monitoring."""
        if self._running:
            return True
        
        if not self._setup_terminal():
            return False
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        return True
    
    def stop(self) -> None:
        """Stop keyboard monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
        self._restore_terminal()
    
    def get_key(self) -> Optional[str]:
        """Get pressed key if any."""
        try:
            return self._key_queue.get_nowait()
        except Empty:
            return None
    
    def clear(self) -> None:
        """Clear key queue."""
        while not self._key_queue.empty():
            try:
                self._key_queue.get_nowait()
            except Empty:
                break


class AudioController:
    """
    Singleton class for managing audio playback with interruption support.
    Provides thread-safe operations for TTS playback with keypress and wake word interruption.
    """
    
    _instance: Optional['AudioController'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'AudioController':
        """Implement singleton pattern with thread safety."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self) -> None:
        """Initialize audio controller."""
        if self._initialized:
            return
        
        self._playing = False
        self._interrupted = False
        self._interrupt_reason: Optional[str] = None
        self._playback_process: Optional[subprocess.Popen] = None
        self._keyboard_monitor = KeyboardMonitor()
        self._wakeword_handler = None
        self._interrupt_keys = ['s', 'q']  # Keys that interrupt playback
        self._callbacks: dict = {
            'on_interrupt': [],
            'on_playback_start': [],
            'on_playback_end': [],
        }
        self._initialized = True
        
        logger.info("Audio controller initialized")
    
    def set_wakeword_handler(self, handler) -> None:
        """
        Set the wake word handler for interrupt detection.
        
        Args:
            handler: WakeWordHandler instance.
        """
        self._wakeword_handler = handler
        if handler:
            handler.register_callback(self._on_wakeword_detected)
            logger.info("Wake word handler connected to audio controller")
    
    def _on_wakeword_detected(self) -> None:
        """Callback when wake word is detected during playback."""
        if self._playing:
            logger.info("Wake word detected during playback - interrupting")
            self._interrupt("wakeword")
    
    def _interrupt(self, reason: str) -> None:
        """
        Interrupt current playback.
        
        Args:
            reason: Reason for interruption ('keypress' or 'wakeword').
        """
        self._interrupted = True
        self._interrupt_reason = reason
        
        # Stop the playback process
        if self._playback_process:
            try:
                self._playback_process.terminate()
                self._playback_process.wait(timeout=1.0)
            except Exception as e:
                logger.debug(f"Error terminating playback: {e}")
                try:
                    self._playback_process.kill()
                except Exception:
                    pass
        
        # Call interrupt callbacks
        for callback in self._callbacks['on_interrupt']:
            try:
                callback(reason)
            except Exception as e:
                logger.error(f"Interrupt callback error: {e}")
    
    def play_audio_interruptible(
        self,
        audio_path: Path,
        allow_keypress: bool = True,
        allow_wakeword: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Play audio file with interrupt support.
        
        Args:
            audio_path: Path to audio file.
            allow_keypress: Allow 's' or 'q' keypress to interrupt.
            allow_wakeword: Allow wake word to interrupt.
        
        Returns:
            Tuple[bool, Optional[str]]: (completed, interrupt_reason)
                - completed: True if played to end, False if interrupted
                - interrupt_reason: 'keypress', 'wakeword', or None
        """
        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return False, None
        
        self._playing = True
        self._interrupted = False
        self._interrupt_reason = None
        
        # Call playback start callbacks
        for callback in self._callbacks['on_playback_start']:
            try:
                callback()
            except Exception as e:
                logger.error(f"Playback start callback error: {e}")
        
        # Start keyboard monitoring if needed
        if allow_keypress:
            self._keyboard_monitor.start()
            self._keyboard_monitor.clear()
        
        # Start wake word listening if handler available
        wakeword_was_listening = False
        if allow_wakeword and self._wakeword_handler:
            wakeword_was_listening = self._wakeword_handler.is_listening
            if not wakeword_was_listening:
                self._wakeword_handler.start_listening()
        
        try:
            # Find available player
            players = [
                (['aplay', str(audio_path)], 'aplay'),
                (['ffplay', '-nodisp', '-autoexit', str(audio_path)], 'ffplay'),
                (['mpg123', str(audio_path)], 'mpg123'),
            ]
            
            for cmd, player_name in players:
                try:
                    logger.debug(f"Trying player: {player_name}")
                    self._playback_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    break
                except FileNotFoundError:
                    continue
            
            if not self._playback_process:
                logger.error("No audio player found")
                return False, None
            
            # Print interrupt hint
            if allow_keypress:
                print("  [Press 's' to skip, or say wake word to interrupt]")
            
            # Monitor for interrupts while playing
            while self._playback_process.poll() is None:
                if self._interrupted:
                    break
                
                # Check for keypress
                if allow_keypress:
                    key = self._keyboard_monitor.get_key()
                    if key and key.lower() in self._interrupt_keys:
                        logger.info(f"Keypress '{key}' detected - interrupting playback")
                        self._interrupt("keypress")
                        break
                
                time.sleep(0.05)
            
            completed = not self._interrupted
            
            # Call playback end callbacks
            for callback in self._callbacks['on_playback_end']:
                try:
                    callback(completed)
                except Exception as e:
                    logger.error(f"Playback end callback error: {e}")
            
            return completed, self._interrupt_reason
            
        except Exception as e:
            logger.error(f"Error during audio playback: {e}", exc_info=True)
            return False, None
            
        finally:
            self._playing = False
            self._playback_process = None
            
            if allow_keypress:
                self._keyboard_monitor.stop()
            
            # Restore wake word listener state
            if allow_wakeword and self._wakeword_handler and not wakeword_was_listening:
                self._wakeword_handler.stop_listening()
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """
        Register a callback for an event.
        
        Args:
            event: Event name ('on_interrupt', 'on_playback_start', 'on_playback_end').
            callback: Function to call.
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def unregister_callback(self, event: str, callback: Callable) -> None:
        """Unregister a callback."""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
    
    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._playing
    
    @property
    def was_interrupted(self) -> bool:
        """Check if last playback was interrupted."""
        return self._interrupted
    
    @property
    def interrupt_reason(self) -> Optional[str]:
        """Get the reason for last interruption."""
        return self._interrupt_reason
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self._playing:
            self._interrupt("cleanup")
        self._keyboard_monitor.stop()
        logger.info("Audio controller cleaned up")


class ThreadManager:
    """
    Manages threading for STT and TTS operations.
    Ensures proper resource sharing and prevents conflicts.
    """
    
    _instance: Optional['ThreadManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'ThreadManager':
        """Implement singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self) -> None:
        """Initialize thread manager."""
        if self._initialized:
            return
        
        self._stt_lock = threading.Lock()
        self._tts_lock = threading.Lock()
        self._audio_lock = threading.Lock()
        self._stt_active = False
        self._tts_active = False
        self._initialized = True
        
        logger.info("Thread manager initialized")
    
    def acquire_stt(self, timeout: float = 5.0) -> bool:
        """
        Acquire STT resource lock.
        
        Args:
            timeout: Timeout in seconds.
        
        Returns:
            bool: True if acquired.
        """
        acquired = self._stt_lock.acquire(timeout=timeout)
        if acquired:
            self._stt_active = True
            logger.debug("STT lock acquired")
        return acquired
    
    def release_stt(self) -> None:
        """Release STT resource lock."""
        try:
            self._stt_active = False
            self._stt_lock.release()
            logger.debug("STT lock released")
        except RuntimeError:
            pass
    
    def acquire_tts(self, timeout: float = 5.0) -> bool:
        """
        Acquire TTS resource lock.
        
        Args:
            timeout: Timeout in seconds.
        
        Returns:
            bool: True if acquired.
        """
        acquired = self._tts_lock.acquire(timeout=timeout)
        if acquired:
            self._tts_active = True
            logger.debug("TTS lock acquired")
        return acquired
    
    def release_tts(self) -> None:
        """Release TTS resource lock."""
        try:
            self._tts_active = False
            self._tts_lock.release()
            logger.debug("TTS lock released")
        except RuntimeError:
            pass
    
    def acquire_audio(self, timeout: float = 5.0) -> bool:
        """Acquire audio resource lock."""
        acquired = self._audio_lock.acquire(timeout=timeout)
        if acquired:
            logger.debug("Audio lock acquired")
        return acquired
    
    def release_audio(self) -> None:
        """Release audio resource lock."""
        try:
            self._audio_lock.release()
            logger.debug("Audio lock released")
        except RuntimeError:
            pass
    
    @property
    def is_stt_active(self) -> bool:
        """Check if STT is currently active."""
        return self._stt_active
    
    @property
    def is_tts_active(self) -> bool:
        """Check if TTS is currently active."""
        return self._tts_active


def main() -> None:
    """Test audio controller."""
    print("Testing Audio Controller")
    print("=" * 40)
    
    controller = AudioController()
    
    # Test with a sample file if it exists
    test_file = Config.AUDIO_DIR / "test_output.wav"
    
    if test_file.exists():
        print(f"\nPlaying: {test_file}")
        print("Press 's' to interrupt...")
        
        completed, reason = controller.play_audio_interruptible(test_file)
        
        if completed:
            print("Playback completed")
        else:
            print(f"Playback interrupted by: {reason}")
    else:
        print(f"\nNo test file at: {test_file}")
        print("Generate one with tts_handler.py first")
    
    controller.cleanup()


if __name__ == '__main__':
    main()
