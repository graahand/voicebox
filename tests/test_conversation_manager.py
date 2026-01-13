"""
Unit tests for the conversation_manager module.
Tests conversation history, logging, and session management.
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.conversation_manager import ConversationManager


class TestConversationManager:
    """Unit tests for ConversationManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh ConversationManager instance for each test."""
        # Reset singleton for testing
        ConversationManager._instance = None
        return ConversationManager()
    
    def test_session_id_generated(self, manager):
        """Test that a session ID is generated on initialization."""
        assert manager.session_id is not None
        assert isinstance(manager.session_id, str)
        assert 'session_' in manager.session_id
    
    def test_add_user_message(self, manager):
        """Test adding a user message to history."""
        manager.add_user_message("Hello, world!")
        history = manager.get_conversation_history()
        
        assert len(history) == 1
        assert history[0]['role'] == 'user'
        assert history[0]['content'] == "Hello, world!"
    
    def test_add_assistant_message(self, manager):
        """Test adding an assistant message to history."""
        manager.add_assistant_message("Hello! How can I help?")
        history = manager.get_conversation_history()
        
        assert len(history) == 1
        assert history[0]['role'] == 'assistant'
        assert history[0]['content'] == "Hello! How can I help?"
    
    def test_conversation_history_order(self, manager):
        """Test that conversation history maintains correct order."""
        manager.add_user_message("Question 1")
        manager.add_assistant_message("Answer 1")
        manager.add_user_message("Question 2")
        manager.add_assistant_message("Answer 2")
        
        history = manager.get_conversation_history()
        
        assert len(history) == 4
        assert history[0]['content'] == "Question 1"
        assert history[1]['content'] == "Answer 1"
        assert history[2]['content'] == "Question 2"
        assert history[3]['content'] == "Answer 2"
    
    def test_get_conversation_history_with_limit(self, manager):
        """Test getting limited conversation history."""
        for i in range(10):
            manager.add_user_message(f"Message {i}")
        
        limited_history = manager.get_conversation_history(max_messages=3)
        
        assert len(limited_history) == 3
        assert limited_history[0]['content'] == "Message 7"
        assert limited_history[2]['content'] == "Message 9"
    
    def test_clear_history(self, manager):
        """Test clearing conversation history."""
        manager.add_user_message("Test message")
        manager.add_assistant_message("Test response")
        
        manager.clear_history()
        history = manager.get_conversation_history()
        
        assert len(history) == 0
    
    def test_log_interaction(self, manager):
        """Test logging an interaction."""
        manager.log_interaction(
            user_query="What is Futuruma?",
            model_response="Futuruma is a tech fest.",
            response_time=1.5,
            status="success"
        )
        
        stats = manager.get_statistics()
        assert stats['total_interactions'] >= 1
    
    def test_save_conversation(self, manager, tmp_path):
        """Test saving conversation to file."""
        from config.config import Config
        original_dir = Config.CONVERSATIONS_DIR
        
        try:
            Config.CONVERSATIONS_DIR = tmp_path
            
            manager.add_user_message("Test message")
            manager.add_assistant_message("Test response")
            
            saved_path = manager.save_conversation()
            
            assert saved_path.exists()
            
            with open(saved_path, 'r') as f:
                data = json.load(f)
            
            assert 'session_id' in data
            assert 'conversation_history' in data
            assert len(data['conversation_history']) == 2
        finally:
            Config.CONVERSATIONS_DIR = original_dir
    
    def test_get_statistics(self, manager):
        """Test getting conversation statistics."""
        manager.log_interaction(
            user_query="Message 1",
            model_response="Response 1",
            response_time=0.5,
            status="success"
        )
        
        stats = manager.get_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_interactions' in stats
        assert stats['total_interactions'] == 1
        assert 'average_response_time_seconds' in stats
        assert 'success_rate_percent' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
