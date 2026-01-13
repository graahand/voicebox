"""
Unit tests for the LangChain RAG handler module.
Tests document processing, embedding generation, and similarity search.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLangChainRAGHandler:
    """Unit tests for LangChainRAGHandler class."""
    
    @pytest.fixture
    def mock_embeddings(self):
        """Create mock embeddings."""
        mock = MagicMock()
        mock.embed_documents.return_value = [[0.1] * 768 for _ in range(5)]
        mock.embed_query.return_value = [0.1] * 768
        return mock
    
    def test_handler_initialization(self):
        """Test that handler initializes without errors."""
        try:
            from modules.langchain_rag_handler import LangChainRAGHandler
            # Reset singleton
            LangChainRAGHandler._instance = None
            handler = LangChainRAGHandler()
            assert handler is not None
        except ImportError as e:
            pytest.skip(f"LangChain dependencies not installed: {e}")
    
    def test_singleton_pattern(self):
        """Test that handler follows singleton pattern."""
        try:
            from modules.langchain_rag_handler import LangChainRAGHandler
            LangChainRAGHandler._instance = None
            handler1 = LangChainRAGHandler()
            handler2 = LangChainRAGHandler()
            assert handler1 is handler2
        except ImportError:
            pytest.skip("LangChain dependencies not installed")
    
    def test_search_returns_tuple(self):
        """Test that search_context returns tuple of context and attributions."""
        try:
            from modules.langchain_rag_handler import LangChainRAGHandler
            LangChainRAGHandler._instance = None
            handler = LangChainRAGHandler()
            
            result = handler.search_context("What is Futuruma?")
            
            assert isinstance(result, tuple)
            assert len(result) == 2
            context, attributions = result
            assert isinstance(context, str)
            assert isinstance(attributions, list)
        except ImportError:
            pytest.skip("LangChain dependencies not installed")
    
    def test_search_with_empty_query(self):
        """Test search with empty query."""
        try:
            from modules.langchain_rag_handler import LangChainRAGHandler
            LangChainRAGHandler._instance = None
            handler = LangChainRAGHandler()
            
            context, attributions = handler.search_context("")
            assert isinstance(context, str)
            assert isinstance(attributions, list)
        except ImportError:
            pytest.skip("LangChain dependencies not installed")
    
    def test_attribution_format(self):
        """Test that attributions have expected format."""
        try:
            from modules.langchain_rag_handler import LangChainRAGHandler
            LangChainRAGHandler._instance = None
            handler = LangChainRAGHandler()
            
            context, attributions = handler.search_context("Tell me about laser tag")
            
            if attributions:
                attr = attributions[0]
                assert 'section' in attr
                assert 'score' in attr
        except ImportError:
            pytest.skip("LangChain dependencies not installed")
    
    def test_is_ready_property(self):
        """Test is_ready property."""
        try:
            from modules.langchain_rag_handler import LangChainRAGHandler
            LangChainRAGHandler._instance = None
            handler = LangChainRAGHandler()
            
            assert isinstance(handler.is_ready, bool)
        except ImportError:
            pytest.skip("LangChain dependencies not installed")
    
    def test_source_attribution_text(self):
        """Test source attribution text generation."""
        try:
            from modules.langchain_rag_handler import LangChainRAGHandler
            LangChainRAGHandler._instance = None
            handler = LangChainRAGHandler()
            
            mock_attributions = [
                {'section': 'Test Section', 'score': 0.95},
                {'section': 'Another Section', 'score': 0.85}
            ]
            
            text = handler.get_source_attribution_text(mock_attributions)
            assert isinstance(text, str)
            if text:
                assert 'Test Section' in text
        except ImportError:
            pytest.skip("LangChain dependencies not installed")
    
    def test_empty_attributions_text(self):
        """Test source attribution text with empty list."""
        try:
            from modules.langchain_rag_handler import LangChainRAGHandler
            LangChainRAGHandler._instance = None
            handler = LangChainRAGHandler()
            
            text = handler.get_source_attribution_text([])
            assert text == ""
        except ImportError:
            pytest.skip("LangChain dependencies not installed")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
