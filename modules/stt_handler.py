"""
STT Handler module for VoiceBox project.
Manages Speech-to-Text using faster-whisper with singleton pattern.
"""

from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config


class STTHandler:
    """
    Singleton class for handling Speech-to-Text with faster-whisper.
    Manages model initialization and transcription with VAD support.
    """
    
    _instance: Optional['STTHandler'] = None
    
    def __new__(cls) -> 'STTHandler':
        """
        Implement singleton pattern.
        
        Returns:
            STTHandler: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """
        Initialize STT handler.
        Only runs once due to singleton pattern.
        """
        if self._initialized:
            return
        
        self._model_size: str = Config.STT_MODEL_SIZE
        self._device: str = Config.STT_DEVICE
        self._compute_type: str = Config.STT_COMPUTE_TYPE
        self._beam_size: int = Config.STT_BEAM_SIZE
        self._vad_filter: bool = Config.STT_VAD_FILTER
        self._model = None
        self._initialized = True
        
        # Initialize the model
        self._init_model()
    
    def _init_model(self) -> None:
        """
        Initialize the faster-whisper model.
        """
        try:
            from faster_whisper import WhisperModel
            
            print(f"Loading Whisper model: {self._model_size}")
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type
            )
            print("Whisper model initialized successfully")
            
        except ImportError as e:
            print(f"Error importing faster-whisper: {e}")
            print("Please install faster-whisper: pip install faster-whisper")
            self._model = None
        except Exception as e:
            print(f"Error initializing STT model: {e}")
            print(f"Trying CPU fallback...")
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(
                    self._model_size,
                    device="cpu",
                    compute_type="int8"
                )
                print("Whisper model initialized on CPU")
            except Exception as fallback_error:
                print(f"CPU fallback failed: {fallback_error}")
                self._model = None
    
    def transcribe_audio(
        self,
        audio_path: Path
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to the audio file.
        
        Returns:
            Tuple[Optional[str], Optional[Dict[str, Any]]]: 
                Transcribed text and info dict, or (None, None) if failed.
        """
        if self._model is None:
            print("STT model not initialized")
            return None, None
        
        if not audio_path.exists():
            print(f"Audio file not found: {audio_path}")
            return None, None
        
        try:
            # Transcribe the audio
            segments, info = self._model.transcribe(
                str(audio_path),
                beam_size=self._beam_size,
                vad_filter=self._vad_filter
            )
            
            # Extract language info
            language_info: Dict[str, Any] = {
                'language': info.language,
                'language_probability': info.language_probability
            }
            
            print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
            
            # Collect all segments into full text
            full_text: str = ""
            segment_list: List[Dict[str, Any]] = []
            
            for segment in segments:
                full_text += segment.text + " "
                segment_list.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text
                })
                print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            
            full_text = full_text.strip()
            
            # Combine info
            result_info: Dict[str, Any] = {
                **language_info,
                'segments': segment_list
            }
            
            return full_text, result_info
            
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None, None
    
    def transcribe_with_vad(
        self,
        audio_path: Path
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Transcribe audio file with Voice Activity Detection.
        
        Args:
            audio_path: Path to the audio file.
        
        Returns:
            Tuple[Optional[str], Optional[Dict[str, Any]]]: 
                Transcribed text and info dict, or (None, None) if failed.
        """
        # VAD is already enabled by default in transcribe_audio
        return self.transcribe_audio(audio_path)
    
    @property
    def model_size(self) -> str:
        """
        Get the model size.
        
        Returns:
            str: The model size.
        """
        return self._model_size
    
    @property
    def device(self) -> str:
        """
        Get the device.
        
        Returns:
            str: The device name.
        """
        return self._device


def main() -> None:
    """
    Main function for testing STT handler.
    """
    Config.ensure_directories()
    
    stt: STTHandler = STTHandler()
    print(f"STT Handler initialized with model: {stt.model_size}")
    print(f"Device: {stt.device}")
    
    # Test transcription (would need an actual audio file)
    print("\nTo test transcription, provide an audio file path")
    print("Example usage:")
    print("  text, info = stt.transcribe_audio(Path('path/to/audio.mp3'))")


if __name__ == '__main__':
    main()
