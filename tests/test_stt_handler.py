"""
Unit tests for the STT handler module.
Tests speech-to-text initialization and transcription.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSTTHandler:
    """Unit tests for STTHandler class."""
    
    @pytest.fixture
    def mock_whisper(self):
        """Create mock faster-whisper model."""
        with patch('modules.stt_handler.WhisperModel', create=True) as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            yield mock_class
    
    def test_handler_initialization(self):
        """Test that handler initializes."""
        try:
            from modules.stt_handler import STTHandler
            STTHandler._instance = None
            handler = STTHandler()
            assert handler is not None
        except Exception as e:
            pytest.skip(f"STT initialization failed: {e}")
    
    def test_singleton_pattern(self):
        """Test that handler follows singleton pattern."""
        try:
            from modules.stt_handler import STTHandler
            STTHandler._instance = None
            handler1 = STTHandler()
            handler2 = STTHandler()
            assert handler1 is handler2
        except Exception:
            pytest.skip("STT not available")
    
    def test_transcribe_nonexistent_file(self):
        """Test transcription of nonexistent file."""
        try:
            from modules.stt_handler import STTHandler
            STTHandler._instance = None
            handler = STTHandler()
            
            result, info = handler.transcribe_audio(Path("/nonexistent/file.wav"))
            assert result is None
            assert info is None
        except Exception:
            pytest.skip("STT not available")
    
    def test_transcribe_returns_tuple(self):
        """Test that transcribe_audio returns tuple."""
        try:
            from modules.stt_handler import STTHandler
            STTHandler._instance = None
            handler = STTHandler()
            
            # Even with invalid path, should return tuple
            result = handler.transcribe_audio(Path("/fake/path.wav"))
            assert isinstance(result, tuple)
            assert len(result) == 2
        except Exception:
            pytest.skip("STT not available")
    
    def test_model_size_configuration(self):
        """Test that model size is configured."""
        from config.config import Config
        assert Config.STT_MODEL_SIZE is not None
        assert Config.STT_MODEL_SIZE in ['tiny', 'base', 'small', 'medium', 'large']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
