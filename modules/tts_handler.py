"""
TTS Handler module for VoiceBox project.
Manages Text-to-Speech using MeloTTS with singleton pattern.
"""

from typing import Optional, Dict
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config


class TTSHandler:
    """
    Singleton class for handling Text-to-Speech with MeloTTS.
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
        
        self._language: str = Config.TTS_LANGUAGE
        self._speaker: str = Config.TTS_SPEAKER
        self._speed: float = Config.TTS_SPEED
        self._device: str = Config.TTS_DEVICE
        self._model = None
        self._speaker_ids: Optional[Dict[str, int]] = None
        self._initialized = True
        
        # Initialize the model
        self._init_model()
    
    def _init_model(self) -> None:
        """
        Initialize the MeloTTS model.
        """
        try:
            from melo.api import TTS
            
            print(f"Initializing MeloTTS model (language: {self._language}, device: {self._device})...")
            self._model = TTS(language=self._language, device=self._device)
            self._speaker_ids = self._model.hps.data.spk2id
            
            print(f"MeloTTS model initialized successfully")
            print(f"Available speakers: {list(self._speaker_ids.keys())}")
            
            # Validate speaker
            if self._speaker not in self._speaker_ids:
                available_speakers: str = ', '.join(self._speaker_ids.keys())
                print(f"Warning: Speaker '{self._speaker}' not found. Available: {available_speakers}")
                # Use first available speaker as fallback
                self._speaker = list(self._speaker_ids.keys())[0]
                print(f"Using fallback speaker: {self._speaker}")
            
        except ImportError as e:
            print(f"Error importing MeloTTS: {e}")
            print("Please install MeloTTS:")
            print("  git clone https://github.com/myshell-ai/MeloTTS.git")
            print("  cd MeloTTS")
            print("  pip install -e .")
            print("  python -m unidic download")
            self._model = None
        except Exception as e:
            print(f"Error initializing TTS model: {e}")
            import traceback
            traceback.print_exc()
            self._model = None
    
    def text_to_speech(
        self,
        text: str,
        output_path: Path,
        speaker: Optional[str] = None,
        speed: Optional[float] = None
    ) -> bool:
        """
        Convert text to speech and save to file.
        
        Args:
            text: The text to convert to speech.
            output_path: Path to save the audio file.
            speaker: Optional speaker override (e.g., 'EN-US', 'EN-BR').
            speed: Optional speed override.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if self._model is None:
            print("TTS model not initialized")
            return False
        
        if not text or not text.strip():
            print("Error: Empty text provided")
            return False
        
        try:
            # Use provided values or defaults
            speaker_to_use: str = speaker or self._speaker
            speed_to_use: float = speed or self._speed
            
            # Validate speaker
            if speaker_to_use not in self._speaker_ids:
                print(f"Error: Speaker '{speaker_to_use}' not found")
                return False
            
            # Get speaker ID
            speaker_id: int = self._speaker_ids[speaker_to_use]
            
            print(f"Generating speech with speaker '{speaker_to_use}' at speed {speed_to_use}...")
            
            # Generate and save audio
            self._model.tts_to_file(
                text=text,
                speaker_id=speaker_id,
                output_path=str(output_path),
                speed=speed_to_use
            )
            
            print(f"Audio saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error generating speech: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_and_save(
        self,
        text: str,
        filename: str = "output.wav",
        speaker: Optional[str] = None,
        speed: Optional[float] = None
    ) -> Optional[Path]:
        """
        Generate speech and save to audio directory.
        
        Args:
            text: The text to convert to speech.
            filename: The filename for the output audio.
            speaker: Optional speaker override.
            speed: Optional speed override.
        
        Returns:
            Optional[Path]: Path to saved audio file, or None if failed.
        """
        output_path: Path = Config.AUDIO_DIR / filename
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        success: bool = self.text_to_speech(text, output_path, speaker, speed)
        
        if success:
            return output_path
        return None
    
    @property
    def speaker(self) -> str:
        """
        Get the current speaker setting.
        
        Returns:
            str: The speaker name.
        """
        return self._speaker
    
    @property
    def language(self) -> str:
        """
        Get the language setting.
        
        Returns:
            str: The language code.
        """
        return self._language
    
    @property
    def available_speakers(self) -> Optional[Dict[str, int]]:
        """
        Get available speakers.
        
        Returns:
            Optional[Dict[str, int]]: Dictionary of speaker names to IDs.
        """
        return self._speaker_ids
    
    @property
    def speed(self) -> float:
        """
        Get the current speed setting.
        
        Returns:
            float: The speech speed.
        """
        return self._speed


def main() -> None:
    """
    Main function for testing TTS handler.
    """
    Config.ensure_directories()
    
    tts: TTSHandler = TTSHandler()
    print(f"\nTTS Handler initialized")
    print(f"Language: {tts.language}")
    print(f"Speaker: {tts.speaker}")
    print(f"Speed: {tts.speed}")
    
    if tts.available_speakers:
        print(f"Available speakers: {list(tts.available_speakers.keys())}")
    
    # Test speech generation
    test_text: str = "Hello! This is a test of the text to speech system using MeloTTS."
    print(f"\nGenerating speech for: {test_text}")
    
    audio_path: Optional[Path] = tts.generate_and_save(test_text, "test_output.wav")
    if audio_path:
        print(f"Speech generated successfully: {audio_path}")
    else:
        print("Failed to generate speech")
    
    # Test different accents if available
    if tts.available_speakers and len(tts.available_speakers) > 1:
        print("\nTesting different accents:")
        for speaker_name in list(tts.available_speakers.keys())[:3]:
            test_file: str = f"test_{speaker_name.lower().replace('-', '_')}.wav"
            print(f"  Generating with {speaker_name}...")
            tts.generate_and_save(test_text, test_file, speaker=speaker_name)


if __name__ == '__main__':
    main()
