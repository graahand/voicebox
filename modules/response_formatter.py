"""
Response Formatter module for VoiceBox project.
Formats LLM responses to be suitable for TTS output.
"""

import re
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from modules.pronunciation_dict import PronunciationDict


class ResponseFormatter:
    """
    Formats LLM responses for Text-to-Speech output.
    Removes or converts elements that don't sound natural when spoken.
    """
    
    # Formatting rules as data structures
    REMOVAL_PATTERNS: List[Dict[str, Any]] = [
        {'pattern': r'\*\*(.+?)\*\*', 'replacement': r'\1', 'description': 'Remove bold markdown'},
        {'pattern': r'\*(.+?)\*', 'replacement': r'\1', 'description': 'Remove italic markdown'},
        {'pattern': r'`(.+?)`', 'replacement': r'\1', 'description': 'Remove inline code markers'},
        {'pattern': r'```[\s\S]*?```', 'replacement': '', 'description': 'Remove code blocks'},
        {'pattern': r'\[(.+?)\]\(.+?\)', 'replacement': r'\1', 'description': 'Convert markdown links to text'},
        {'pattern': r'#+\s+', 'replacement': '', 'description': 'Remove markdown headers'},
        {'pattern': r'^\s*[-*+]\s+', 'replacement': '', 'description': 'Remove bullet points'},
        {'pattern': r'^\s*\d+\.\s+', 'replacement': '', 'description': 'Remove numbered lists'},
    ]
    
    REPLACEMENT_PATTERNS: List[Dict[str, Any]] = [
        {'pattern': r'\n+', 'replacement': ' ', 'description': 'Replace newlines with spaces'},
        {'pattern': r'\s+', 'replacement': ' ', 'description': 'Collapse multiple spaces'},
        {'pattern': r'&', 'replacement': 'and', 'description': 'Replace ampersand'},
        {'pattern': r'%', 'replacement': ' percent', 'description': 'Replace percent symbol'},
        {'pattern': r'\$', 'replacement': 'dollars', 'description': 'Replace dollar sign'},
        {'pattern': r'@', 'replacement': 'at', 'description': 'Replace at symbol'},
    ]
    
    def __init__(self) -> None:
        """
        Initialize the response formatter.
        """
        pass
    
    def format_for_speech(self, text: str) -> str:
        """
        Format text to be suitable for speech synthesis.
        
        Args:
            text: The raw text from LLM.
        
        Returns:
            str: Formatted text suitable for TTS.
        """
        formatted_text: str = text
        
        # Apply removal patterns
        for rule in self.REMOVAL_PATTERNS:
            formatted_text = re.sub(
                rule['pattern'],
                rule['replacement'],
                formatted_text,
                flags=re.MULTILINE
            )
        
        # Apply replacement patterns
        for rule in self.REPLACEMENT_PATTERNS:
            formatted_text = re.sub(
                rule['pattern'],
                rule['replacement'],
                formatted_text
            )
        
        # Clean up the text
        formatted_text = self._clean_text(formatted_text)
        
        # Apply pronunciation replacements for difficult words
        formatted_text = PronunciationDict.replace_words(formatted_text)
        
        return formatted_text
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Text to clean.
        
        Returns:
            str: Cleaned text.
        """
        # Strip whitespace
        text = text.strip()
        
        # Remove multiple punctuation
        text = re.sub(r'([.!?])+', r'\1', text)
        
        # Ensure proper spacing after punctuation
        text = re.sub(r'([.!?,;:])(\S)', r'\1 \2', text)
        
        # Remove parenthetical content that might not sound good
        # (Keep this commented out as some parenthetical might be important)
        # text = re.sub(r'\([^)]*\)', '', text)
        
        return text
    
    def limit_length(self, text: str, max_sentences: int = 5) -> str:
        """
        Limit response to a maximum number of sentences.
        
        Args:
            text: The text to limit.
            max_sentences: Maximum number of sentences to keep.
        
        Returns:
            str: Limited text.
        """
        # Split by sentence endings
        sentences: List[str] = re.split(r'(?<=[.!?])\s+', text)
        
        # Take only first max_sentences
        limited_sentences: List[str] = sentences[:max_sentences]
        
        return ' '.join(limited_sentences)
    
    def remove_citations(self, text: str) -> str:
        """
        Remove citation markers and reference numbers.
        
        Args:
            text: Text with citations.
        
        Returns:
            str: Text without citations.
        """
        # Remove [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove (source: ...), (ref: ...), etc.
        text = re.sub(r'\([Ss]ource:.*?\)', '', text)
        text = re.sub(r'\([Rr]ef:.*?\)', '', text)
        
        return text
    
    def format_full_response(
        self,
        text: str,
        max_sentences: Optional[int] = None
    ) -> str:
        """
        Apply all formatting steps to a response.
        
        Args:
            text: Raw LLM response.
            max_sentences: Optional limit on number of sentences.
        
        Returns:
            str: Fully formatted response ready for TTS.
        """
        # Remove citations
        formatted: str = self.remove_citations(text)
        
        # Format for speech
        formatted = self.format_for_speech(formatted)
        
        # Limit length if specified
        if max_sentences:
            formatted = self.limit_length(formatted, max_sentences)
        
        return formatted


# Type hint for optional import
from typing import Optional


def main() -> None:
    """
    Main function for testing response formatter.
    """
    formatter: ResponseFormatter = ResponseFormatter()
    
    # Test cases
    test_responses: List[str] = [
        "**Hello!** I'm here to help you. Visit [this link](https://example.com) for more info.",
        "Here are the steps:\n1. First step\n2. Second step\n3. Third step",
        "The result is 50%. That's a good score! You can reach me @ email.",
        "This is a `code example` with some **bold** and *italic* text.",
    ]
    
    print("Response Formatter Test Cases:\n")
    
    for i, response in enumerate(test_responses, 1):
        print(f"Test {i}:")
        print(f"Original: {response}")
        formatted: str = formatter.format_full_response(response)
        print(f"Formatted: {formatted}")
        print()


if __name__ == '__main__':
    main()
