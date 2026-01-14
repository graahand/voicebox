"""
TTS Handler module for VoiceBox project.
Manages Text-to-Speech using PiperTTS with singleton pattern.
"""

from typing import Optional
from pathlib import Path
import sys
import wave

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config
from config.logger import get_logger, suppress_library_warnings

# Suppress third-party library warnings
suppress_library_warnings()

logger = get_logger('tts')


class TTSHandler:
    """
    Singleton class for handling Text-to-Speech with PiperTTS.
    Manages model initialization and audio generation.
    """
    
    _instance: Optional['TTSHandler'] = None
    
    def __new__(cls) -> 'TTSHandler':
        """
        Implement singleton pattern.
        
        Returns:
            TTSHandler: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """
        Initialize TTS handler.
        Only runs once due to singleton pattern.
        """
        if self._initialized:
            return
        
        self._voice_model: str = Config.TTS_VOICE_MODEL
        self._voice_path: str = Config.TTS_VOICE_PATH
        self._speed: float = Config.TTS_SPEED
        self._volume: float = Config.TTS_VOLUME
        self._use_cuda: bool = Config.TTS_USE_CUDA
        self._voice = None
        self._initialized = True
        
        # Initialize the model
        self._init_model()
    
    def _init_model(self) -> None:
        """
        Initialize the PiperTTS model.
        """
        try:
            from piper import PiperVoice
            
            # Determine voice path
            if self._voice_path:
                voice_file = Path(self._voice_path)
            else:
                # Auto-download voice if not specified
                voice_file = self._download_voice()
            
            if not voice_file or not voice_file.exists():
                logger.error(f"Voice file not found: {voice_file}")
                self._voice = None
                return
            
            logger.info(f"Loading PiperTTS voice: {voice_file}")
            logger.info(f"CUDA enabled: {self._use_cuda}")
            
            # Load voice with optional CUDA support
            self._voice = PiperVoice.load(str(voice_file), use_cuda=self._use_cuda)
            
            logger.info("PiperTTS voice loaded successfully")
            logger.info(f"Voice model: {self._voice_model}")
            logger.info(f"Speed: {self._speed}x, Volume: {self._volume}")
            
        except ImportError as e:
            logger.error("Error importing PiperTTS", exc_info=True)
            print(f"Error importing PiperTTS: {e}")
            print("Please install PiperTTS:")
            print("  pip install piper-tts")
            print("For CUDA support:")
            print("  pip install onnxruntime-gpu")
            self._voice = None
        except Exception as e:
            logger.error("Error initializing TTS voice", exc_info=True)
            print(f"Error initializing TTS voice: {e}")
            import traceback
            traceback.print_exc()
            self._voice = None
    
    def _download_voice(self) -> Optional[Path]:
        """
        Download the specified voice model.
        
        Returns:
            Optional[Path]: Path to downloaded voice file.
        """
        try:
            import subprocess
            import glob
            
            logger.info(f"Downloading voice model: {self._voice_model}")
            result = subprocess.run(
                [sys.executable, "-m", "piper.download_voices", self._voice_model],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to download voice: {result.stderr}")
                logger.info(f"Download output: {result.stdout}")
                return None
            
            logger.info(f"Download completed: {result.stdout}")
            
            # Try multiple common locations for piper voices
            possible_locations = [
                Path(f"./{self._voice_model}.onnx"),  # Current directory (most common)
                Path(f"{self._voice_model}.onnx"),
                Path.home() / ".local" / "share" / "piper-voices" / f"{self._voice_model}.onnx",
                Path.home() / ".local" / "share" / "piper" / f"{self._voice_model}.onnx",
                Path(f"/usr/share/piper-voices/{self._voice_model}.onnx"),
            ]
            
            # Also search using glob pattern
            search_patterns = [
                str(Path.home() / ".local" / "share" / "piper-voices" / "**" / f"{self._voice_model}.onnx"),
                str(Path.home() / ".local" / "share" / "piper" / "**" / f"{self._voice_model}.onnx"),
            ]
            
            # Check known locations first
            for voice_file in possible_locations:
                if voice_file.exists():
                    logger.info(f"Voice found at: {voice_file}")
                    return voice_file
            
            # Search recursively
            for pattern in search_patterns:
                matches = glob.glob(pattern, recursive=True)
                if matches:
                    voice_file = Path(matches[0])
                    logger.info(f"Voice found at: {voice_file}")
                    return voice_file
            
            # If still not found, print the download output for debugging
            logger.warning(f"Voice file not found after download")
            logger.info(f"Searched locations: {[str(p) for p in possible_locations]}")
            logger.info(f"Download stdout: {result.stdout}")
            return None
            
        except Exception as e:
            logger.error(f"Error downloading voice: {e}", exc_info=True)
            return None
    
    def text_to_speech(
        self,
        text: str,
        output_path: Path,
        speed: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """
        Convert text to speech and save to file.
        
        Args:
            text: The text to convert to speech.
            output_path: Path to save the audio file.
            speed: Optional speed override (length_scale: higher = slower).
            volume: Optional volume override (0.0 to 1.0).
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if self._voice is None:
            logger.error("TTS voice not initialized")
            print("TTS voice not initialized")
            return False
        
        if not text or not text.strip():
            logger.error("Empty text provided for TTS")
            print("Error: Empty text provided")
            return False
        
        try:
            from piper.voice import SynthesisConfig
            
            # Use provided values or defaults
            speed_to_use: float = speed or self._speed
            volume_to_use: float = volume or self._volume
            
            logger.info(f"Generating speech (speed={speed_to_use}x, volume={volume_to_use}, length={len(text)} chars)")
            logger.debug(f"Text to synthesize: {text[:100]}...")
            
            # Create synthesis configuration
            syn_config = SynthesisConfig(
                volume=volume_to_use,
                length_scale=speed_to_use,  # Higher = slower
                noise_scale=0.667,
                noise_w_scale=0.8,
                normalize_audio=True
            )
            
            # Generate and save audio using wave file
            with wave.open(str(output_path), "wb") as wav_file:
                self._voice.synthesize_wav(text, wav_file, syn_config=syn_config)
            
            logger.info(f"Audio saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error("Error generating speech", exc_info=True)
            print(f"Error generating speech: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_and_save(
        self,
        text: str,
        filename: str = "output.wav",
        speed: Optional[float] = None,
        volume: Optional[float] = None
    ) -> Optional[Path]:
        """
        Generate speech and save to audio directory.
        
        Args:
            text: The text to convert to speech.
            filename: The filename for the output audio.
            speed: Optional speed override.
            volume: Optional volume override.
        
        Returns:
            Optional[Path]: Path to saved audio file, or None if failed.
        """
        output_path: Path = Config.AUDIO_DIR / filename
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        success: bool = self.text_to_speech(text, output_path, speed, volume)
        
        if success:
            return output_path
        return None
    
    @property
    def voice_model(self) -> str:
        """
        Get the voice model name.
        
        Returns:
            str: The voice model name.
        """
        return self._voice_model
    
    @property
    def speed(self) -> float:
        """
        Get the current speed setting.
        
        Returns:
            float: The speech speed.
        """
        return self._speed
    
    @property
    def volume(self) -> float:
        """
        Get the current volume setting.
        
        Returns:
            float: The volume level.
        """
        return self._volume


def main() -> None:
    """
    Main function for testing TTS handler.
    """
    Config.ensure_directories()
    
    tts: TTSHandler = TTSHandler()
    print(f"\nTTS Handler initialized")
    print(f"Voice Model: {tts.voice_model}")
    print(f"Speed: {tts.speed}x")
    print(f"Volume: {tts.volume}")
    
    # Test speech generation
    test_text: str = "Hello! This is a test of the text to speech system using PiperTTS."
    print(f"\nGenerating speech for: {test_text}")
    
    audio_path: Optional[Path] = tts.generate_and_save(test_text, "test_output.wav")
    if audio_path:
        print(f"Speech generated successfully: {audio_path}")
    else:
        print("Failed to generate speech")
    
    # Test different speeds
    print("\nTesting different speeds:")
    for speed in [0.75, 1.0, 1.5]:
        test_file: str = f"test_speed_{speed}.wav"
        print(f"  Generating at {speed}x speed...")
        tts.generate_and_save(test_text, test_file, speed=speed)


if __name__ == '__main__':
    main()
