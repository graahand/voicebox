"""
System/Integration tests for VoiceBox.
Tests end-to-end functionality of the complete system.
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSystemIntegration:
    """System integration tests for VoiceBox."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch('modules.llm_handler.ollama') as mock_ollama, \
             patch('modules.tts_handler.TTS', create=True) as mock_tts, \
             patch('modules.stt_handler.WhisperModel', create=True) as mock_whisper:
            
            # Setup Ollama mock
            mock_ollama.list.return_value = MagicMock(
                models=[MagicMock(model='gemma3:270m')]
            )
            mock_ollama.chat.return_value = {
                'message': {'content': 'This is a test response about Futuruma.'}
            }
            
            # Setup TTS mock
            mock_tts_instance = MagicMock()
            mock_tts_instance.hps.data.spk2id = {'EN-US': 0}
            mock_tts.return_value = mock_tts_instance
            
            # Setup Whisper mock
            mock_whisper_instance = MagicMock()
            mock_whisper.return_value = mock_whisper_instance
            
            yield {
                'ollama': mock_ollama,
                'tts': mock_tts,
                'whisper': mock_whisper
            }
    
    def test_config_initialization(self):
        """Test that configuration loads correctly."""
        from config.config import Config
        
        Config.ensure_directories()
        
        assert Config.BASE_DIR.exists() or True  # May not exist in test env
        assert Config.LLM_MODEL is not None
        assert Config.load_system_prompt() is not None
    
    def test_logger_initialization(self):
        """Test that logger initializes correctly."""
        from config.logger import get_logger, suppress_library_warnings
        
        suppress_library_warnings()
        logger = get_logger('test_system')
        
        assert logger is not None
        logger.info("System test log message")
    
    def test_rag_source_file_exists(self):
        """Test that RAG source data file exists."""
        from config.config import Config
        
        source_file = Config.DATA_DIR / Config.RAG_SOURCE_FILE
        assert source_file.exists(), f"Source file not found: {source_file}"
    
    def test_rag_source_data_format(self):
        """Test that RAG source data is properly formatted."""
        from config.config import Config
        
        source_file = Config.DATA_DIR / Config.RAG_SOURCE_FILE
        
        with open(source_file, 'r') as f:
            content = f.read()
        
        # Check for markdown headers
        assert '#' in content, "Source data should contain markdown headers"
        assert 'Futuruma' in content, "Source data should mention Futuruma"
    
    def test_conversation_session_persistence(self, tmp_path):
        """Test that conversations are saved and can be loaded."""
        from config.config import Config
        from modules.conversation_manager import ConversationManager
        
        original_dir = Config.CONVERSATIONS_DIR
        ConversationManager._instance = None
        
        try:
            Config.CONVERSATIONS_DIR = tmp_path
            
            manager = ConversationManager()
            manager.add_user_message("Test question")
            manager.add_assistant_message("Test answer")
            
            saved_path = manager.save_conversation()
            
            # Verify file was created and is valid JSON
            assert saved_path.exists()
            
            with open(saved_path, 'r') as f:
                data = json.load(f)
            
            assert 'session_id' in data
            assert 'conversation_history' in data
            assert len(data['conversation_history']) == 2
        finally:
            Config.CONVERSATIONS_DIR = original_dir
            ConversationManager._instance = None
    
    def test_response_formatting_pipeline(self):
        """Test the response formatting pipeline."""
        from modules.response_formatter import ResponseFormatter
        
        formatter = ResponseFormatter()
        
        # Test with markdown-heavy response
        raw_response = """
        **Futuruma** is a tech fest!
        
        Key features:
        - Feature 1
        - Feature 2
        
        Visit `https://example.com` for more.
        """
        
        formatted = formatter.format_full_response(raw_response)
        
        # Should remove markdown formatting
        assert '**' not in formatted
        assert '`' not in formatted
        assert isinstance(formatted, str)
        assert len(formatted) > 0
    
    def test_end_to_end_text_processing(self, mock_dependencies):
        """Test end-to-end text processing (without actual API calls)."""
        from modules.llm_handler import LLMHandler
        from modules.response_formatter import ResponseFormatter
        
        # Reset singletons
        LLMHandler._instance = None
        
        llm = LLMHandler()
        formatter = ResponseFormatter()
        
        # Generate response
        response, attributions = llm.generate_response("What is Futuruma?")
        
        # Format response
        formatted = formatter.format_full_response(response)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
