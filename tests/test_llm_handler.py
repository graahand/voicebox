"""
Unit tests for the LLM handler module.
Tests LLM initialization, response generation, and RAG integration.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLLMHandler:
    """Unit tests for LLMHandler class."""
    
    @pytest.fixture
    def mock_ollama(self):
        """Create mock Ollama client."""
        with patch('modules.llm_handler.ollama') as mock:
            mock.list.return_value = MagicMock(
                models=[MagicMock(model='gemma3:270m')]
            )
            mock.chat.return_value = {
                'message': {'content': 'Test response from LLM'}
            }
            yield mock
    
    def test_handler_initialization(self, mock_ollama):
        """Test that handler initializes without errors."""
        from modules.llm_handler import LLMHandler
        LLMHandler._instance = None
        
        handler = LLMHandler()
        assert handler is not None
    
    def test_singleton_pattern(self, mock_ollama):
        """Test that handler follows singleton pattern."""
        from modules.llm_handler import LLMHandler
        LLMHandler._instance = None
        
        handler1 = LLMHandler()
        handler2 = LLMHandler()
        assert handler1 is handler2
    
    def test_model_name_property(self, mock_ollama):
        """Test model_name property."""
        from modules.llm_handler import LLMHandler
        LLMHandler._instance = None
        
        handler = LLMHandler()
        assert isinstance(handler.model_name, str)
        assert len(handler.model_name) > 0
    
    def test_system_prompt_property(self, mock_ollama):
        """Test system_prompt property."""
        from modules.llm_handler import LLMHandler
        LLMHandler._instance = None
        
        handler = LLMHandler()
        assert isinstance(handler.system_prompt, str)
        assert len(handler.system_prompt) > 0
    
    def test_generate_response_returns_tuple(self, mock_ollama):
        """Test that generate_response returns tuple."""
        from modules.llm_handler import LLMHandler
        LLMHandler._instance = None
        
        handler = LLMHandler()
        result = handler.generate_response("Hello")
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        response, attributions = result
        assert isinstance(response, str)
        assert isinstance(attributions, list)
    
    def test_generate_response_with_history(self, mock_ollama):
        """Test response generation with conversation history."""
        from modules.llm_handler import LLMHandler
        LLMHandler._instance = None
        
        handler = LLMHandler()
        history = [
            {'role': 'user', 'content': 'Previous question'},
            {'role': 'assistant', 'content': 'Previous answer'}
        ]
        
        response, _ = handler.generate_response("Follow up", history)
        assert isinstance(response, str)
    
    def test_generate_response_handles_error(self, mock_ollama):
        """Test error handling in response generation."""
        from modules.llm_handler import LLMHandler
        LLMHandler._instance = None
        
        mock_ollama.chat.side_effect = Exception("API Error")
        
        handler = LLMHandler()
        response, _ = handler.generate_response("Test")
        
        assert "trouble" in response.lower() or "apologize" in response.lower()
    
    def test_rag_enabled_property(self, mock_ollama):
        """Test rag_enabled property."""
        from modules.llm_handler import LLMHandler
        LLMHandler._instance = None
        
        handler = LLMHandler()
        assert isinstance(handler.rag_enabled, bool)
    
    def test_empty_input_handling(self, mock_ollama):
        """Test handling of empty input."""
        from modules.llm_handler import LLMHandler
        LLMHandler._instance = None
        
        handler = LLMHandler()
        response, _ = handler.generate_response("")
        assert isinstance(response, str)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
