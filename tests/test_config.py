"""
Unit tests for the config module.
Tests configuration loading, directory creation, and system prompt handling.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import Config


class TestConfig:
    """Unit tests for Config class."""
    
    def test_base_directories_exist(self):
        """Test that base directory paths are properly defined."""
        assert Config.BASE_DIR is not None
        assert isinstance(Config.BASE_DIR, Path)
        assert Config.CONFIG_DIR is not None
        assert Config.DATA_DIR is not None
        assert Config.LOGS_DIR is not None
    
    def test_data_subdirectories_defined(self):
        """Test that data subdirectories are properly defined."""
        assert Config.AUDIO_DIR is not None
        assert Config.CONVERSATIONS_DIR is not None
        assert Config.AUDIO_DIR.parent == Config.DATA_DIR
        assert Config.CONVERSATIONS_DIR.parent == Config.DATA_DIR
    
    def test_llm_settings_have_defaults(self):
        """Test that LLM settings have default values."""
        assert Config.LLM_MODEL is not None
        assert isinstance(Config.LLM_MODEL, str)
        assert Config.OLLAMA_HOST is not None
        assert Config.MAX_RESPONSE_LENGTH > 0
        assert 0 <= Config.TEMPERATURE <= 2
    
    def test_tts_settings_have_defaults(self):
        """Test that TTS settings have default values."""
        assert Config.TTS_LANGUAGE is not None
        assert Config.TTS_SPEAKER is not None
        assert Config.TTS_SPEED > 0
        assert Config.TTS_DEVICE is not None
    
    def test_stt_settings_have_defaults(self):
        """Test that STT settings have default values."""
        assert Config.STT_MODEL_SIZE is not None
        assert Config.STT_DEVICE is not None
        assert Config.STT_BEAM_SIZE > 0
        assert isinstance(Config.STT_VAD_FILTER, bool)
    
    def test_rag_settings_have_defaults(self):
        """Test that RAG settings have default values."""
        assert Config.RAG_TOP_K > 0
        assert 0 <= Config.RAG_SCORE_THRESHOLD <= 1
        assert Config.RAG_MAX_CONTEXT_LENGTH > 0
        assert Config.RAG_EMBEDDING_MODEL is not None
        assert Config.RAG_VECTOR_DIMENSION > 0
    
    def test_ensure_directories_creates_dirs(self, tmp_path):
        """Test that ensure_directories creates required directories."""
        # Temporarily override paths
        original_data = Config.DATA_DIR
        original_logs = Config.LOGS_DIR
        original_audio = Config.AUDIO_DIR
        original_conv = Config.CONVERSATIONS_DIR
        original_config = Config.CONFIG_DIR
        
        try:
            Config.DATA_DIR = tmp_path / "data"
            Config.LOGS_DIR = tmp_path / "logs"
            Config.AUDIO_DIR = tmp_path / "data" / "audio"
            Config.CONVERSATIONS_DIR = tmp_path / "data" / "conversations"
            Config.CONFIG_DIR = tmp_path / "config"
            
            Config.ensure_directories()
            
            assert Config.DATA_DIR.exists()
            assert Config.LOGS_DIR.exists()
            assert Config.AUDIO_DIR.exists()
            assert Config.CONVERSATIONS_DIR.exists()
        finally:
            # Restore original paths
            Config.DATA_DIR = original_data
            Config.LOGS_DIR = original_logs
            Config.AUDIO_DIR = original_audio
            Config.CONVERSATIONS_DIR = original_conv
            Config.CONFIG_DIR = original_config
    
    def test_load_system_prompt_returns_string(self):
        """Test that load_system_prompt returns a string."""
        prompt = Config.load_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_load_system_prompt_fallback_on_missing_file(self, tmp_path):
        """Test that load_system_prompt returns default when file missing."""
        original_path = Config.SYSTEM_PROMPT_PATH
        try:
            Config.SYSTEM_PROMPT_PATH = tmp_path / "nonexistent.txt"
            prompt = Config.load_system_prompt()
            assert isinstance(prompt, str)
            assert len(prompt) > 0
        finally:
            Config.SYSTEM_PROMPT_PATH = original_path
    
    def test_get_config_dict_returns_dict(self):
        """Test that get_config_dict returns a dictionary with expected keys."""
        config_dict = Config.get_config_dict()
        assert isinstance(config_dict, dict)
        assert 'llm_model' in config_dict
        assert 'tts_language' in config_dict
        assert 'stt_model_size' in config_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
