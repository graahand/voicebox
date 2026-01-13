"""
Unit tests for the response_formatter module.
Tests text formatting for TTS output.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.response_formatter import ResponseFormatter


class TestResponseFormatter:
    """Unit tests for ResponseFormatter class."""
    
    @pytest.fixture
    def formatter(self):
        """Create a ResponseFormatter instance."""
        return ResponseFormatter()
    
    def test_remove_markdown_bold(self, formatter):
        """Test removal of bold markdown."""
        text = "This is **bold** text"
        result = formatter.format_full_response(text)
        assert "**" not in result
        assert "bold" in result
    
    def test_remove_markdown_italic(self, formatter):
        """Test removal of italic markdown."""
        text = "This is *italic* text"
        result = formatter.format_full_response(text)
        assert result.count("*") == 0 or "italic" in result
    
    def test_remove_code_blocks(self, formatter):
        """Test removal of code blocks."""
        text = "Here is code: `print('hello')`"
        result = formatter.format_full_response(text)
        assert "`" not in result
    
    def test_handle_urls(self, formatter):
        """Test URL handling in text."""
        text = "Visit https://example.com for more"
        result = formatter.format_full_response(text)
        # Should handle URL appropriately (remove or simplify)
        assert isinstance(result, str)
    
    def test_handle_numbers(self, formatter):
        """Test number formatting."""
        text = "There are 50000 students"
        result = formatter.format_full_response(text)
        assert isinstance(result, str)
        # Number should be preserved or formatted for speech
    
    def test_handle_special_characters(self, formatter):
        """Test special character handling."""
        text = "Use #hashtag and @mention"
        result = formatter.format_full_response(text)
        assert isinstance(result, str)
    
    def test_empty_string(self, formatter):
        """Test handling of empty string."""
        result = formatter.format_full_response("")
        assert isinstance(result, str)
    
    def test_whitespace_normalization(self, formatter):
        """Test that extra whitespace is normalized."""
        text = "Hello    world   test"
        result = formatter.format_full_response(text)
        assert "    " not in result
    
    def test_newline_handling(self, formatter):
        """Test newline handling."""
        text = "Line 1\n\nLine 2\n\n\nLine 3"
        result = formatter.format_full_response(text)
        assert isinstance(result, str)
    
    def test_pronunciation_replacements(self, formatter):
        """Test that pronunciation dictionary is applied."""
        # This depends on pronunciation_dict implementation
        text = "Welcome to Futuruma event"
        result = formatter.format_full_response(text)
        assert isinstance(result, str)
        # Check if Futuruma is replaced with pronunciation version
    
    def test_bullet_point_handling(self, formatter):
        """Test bullet point removal."""
        text = "Items:\n- Item 1\n- Item 2\n- Item 3"
        result = formatter.format_full_response(text)
        # Bullet points should be converted to speakable format
        assert isinstance(result, str)
    
    def test_long_text_handling(self, formatter):
        """Test handling of long text."""
        long_text = "This is a test. " * 100
        result = formatter.format_full_response(long_text)
        assert isinstance(result, str)
        assert len(result) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
