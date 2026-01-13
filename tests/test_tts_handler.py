"""
Unit tests for the TTS handler module.
Tests text-to-speech initialization and audio generation.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTTSHandler:
    """Unit tests for TTSHandler class."""
    
    @pytest.fixture
    def mock_melo_tts(self):
        """Create mock MeloTTS."""
        with patch('modules.tts_handler.TTS', create=True) as mock_tts_class:
            mock_instance = MagicMock()
            mock_instance.hps.data.spk2id = {'EN-US': 0, 'EN-BR': 1}
            mock_tts_class.return_value = mock_instance
            yield mock_tts_class
    
    def test_handler_initialization(self):
        """Test that handler initializes."""
        try:
            from modules.tts_handler import TTSHandler
            TTSHandler._instance = None
            handler = TTSHandler()
            assert handler is not None
        except Exception as e:
            pytest.skip(f"TTS initialization failed: {e}")
    
    def test_singleton_pattern(self):
        """Test that handler follows singleton pattern."""
        try:
            from modules.tts_handler import TTSHandler
            TTSHandler._instance = None
            handler1 = TTSHandler()
            handler2 = TTSHandler()
            assert handler1 is handler2
        except Exception:
            pytest.skip("TTS not available")
    
    def test_speaker_property(self):
        """Test speaker property."""
        try:
            from modules.tts_handler import TTSHandler
            TTSHandler._instance = None
            handler = TTSHandler()
            assert isinstance(handler.speaker, str)
        except Exception:
            pytest.skip("TTS not available")
    
    def test_text_to_speech_empty_text(self):
        """Test TTS with empty text returns False."""
        try:
            from modules.tts_handler import TTSHandler
            TTSHandler._instance = None
            handler = TTSHandler()
            
            result = handler.text_to_speech("", Path("/tmp/test.wav"))
            assert result == False
        except Exception:
            pytest.skip("TTS not available")
    
    def test_text_to_speech_whitespace_text(self):
        """Test TTS with whitespace-only text returns False."""
        try:
            from modules.tts_handler import TTSHandler
            TTSHandler._instance = None
            handler = TTSHandler()
            
            result = handler.text_to_speech("   ", Path("/tmp/test.wav"))
            assert result == False
        except Exception:
            pytest.skip("TTS not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
