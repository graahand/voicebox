"""
RAG Handler module for VoiceBox project.
Manages Retrieval-Augmented Generation for Futuruma event information.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
import re

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config


class RAGHandler:
    """
    Singleton class for handling RAG operations.
    Loads and searches through source documents for relevant context.
    """
    
    _instance: Optional['RAGHandler'] = None
    
    def __new__(cls) -> 'RAGHandler':
        """
        Implement singleton pattern.
        
        Returns:
            RAGHandler: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, source_file: Optional[Path] = None) -> None:
        """
        Initialize RAG handler.
        Only runs once due to singleton pattern.
        
        Args:
            source_file: Path to source data file. Defaults to data/source_data.md
        """
        if self._initialized:
            return
        
        if source_file is None:
            source_file = Config.DATA_DIR / "source_data.md"
        
        self._source_file = source_file
        self._document_sections: Dict[str, str] = {}
        self._full_text: str = ""
        self._top_k: int = Config.RAG_TOP_K
        self._min_score: float = Config.RAG_MIN_SCORE
        self._keyword_boost: float = Config.RAG_KEYWORD_BOOST
        self._max_context_length: int = Config.RAG_MAX_CONTEXT_LENGTH
        self._initialized = True
        
        # Load the source document
        self._load_document()
    
    def _load_document(self) -> None:
        """
        Load and parse the source document into sections.
        """
        try:
            if not self._source_file.exists():
                print(f"Warning: Source file not found: {self._source_file}")
                return
            
            with open(self._source_file, 'r', encoding='utf-8') as file:
                self._full_text = file.read()
            
            # Parse document into sections by headers
            self._parse_sections()
            
            print(f"RAG: Loaded document from {self._source_file}")
            print(f"RAG: Parsed {len(self._document_sections)} sections")
            
        except Exception as e:
            print(f"Error loading RAG document: {e}")
    
    def _parse_sections(self) -> None:
        """
        Parse document into sections based on markdown headers.
        """
        # Split by headers (## or ###)
        lines = self._full_text.split('\n')
        current_section = "introduction"
        current_content = []
        
        for line in lines:
            # Check if line is a header
            if line.startswith('##'):
                # Save previous section
                if current_content:
                    self._document_sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line.strip('#').strip().lower()
                current_content = [line]
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            self._document_sections[current_section] = '\n'.join(current_content).strip()
    
    def search_context(self, query: str, max_sections: Optional[int] = None) -> str:
        """
        Search for relevant context based on query.
        
        Args:
            query: The user's query.
            max_sections: Maximum number of sections to return (uses config if None).
        
        Returns:
            str: Relevant context from the document.
        """
        if not self._document_sections:
            return ""
        
        if max_sections is None:
            max_sections = self._top_k
        
        query_lower = query.lower()
        
        # Keywords to check for Futuruma-related queries
        futuruma_keywords = [
            'futuruma', 'future-rama', 'event', 'tech fest', 'nepal', 'project', 'robotics',
            'ai', 'cybersecurity', 'venue', 'city', 'cities', 'history',
            'ing skill academy', 'skill museum', 'smarc', 's-mark', 'organizer',
            'dermascan', 'derma scan', 'laser tag', 'cybercentric', 'maths assistant',
            'kathmandu', 'pokhara', 'chitwan', 'biratnagar', 'butwal',
            'what is', 'tell me about', 'information about', 'showcase'
        ]
        
        # Check if query is related to Futuruma
        is_futuruma_query = any(keyword in query_lower for keyword in futuruma_keywords)
        
        if not is_futuruma_query:
            return ""  # Return empty if not related to Futuruma
        
        # Score each section based on keyword matches
        scored_sections = []
        
        for section_name, section_content in self._document_sections.items():
            score = 0
            section_lower = section_content.lower()
            
            # Check how many query words appear in section
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 3:  # Only check words longer than 3 chars
                    score += section_lower.count(word)
            
            # Boost score for section name matches (using config parameter)
            for word in query_words:
                if word in section_name:
                    score += self._keyword_boost
            
            # Only include sections above minimum score threshold
            if score >= self._min_score:
                scored_sections.append((score, section_name, section_content))
        
        # Sort by score (highest first)
        scored_sections.sort(reverse=True, key=lambda x: x[0])
        
        # Return top sections
        if not scored_sections:
            # If no specific matches, return introduction
            intro_text = self._full_text[:self._max_context_length]
            return intro_text + ("..." if len(self._full_text) > self._max_context_length else "")
        
        # Combine top sections up to max context length
        relevant_sections = scored_sections[:max_sections]
        context_parts = []
        current_length = 0
        
        for _, _, content in relevant_sections:
            if current_length + len(content) <= self._max_context_length:
                context_parts.append(content)
                current_length += len(content)
            else:
                # Add partial content if space available
                remaining_space = self._max_context_length - current_length
                if remaining_space > 100:  # Only add if substantial space left
                    context_parts.append(content[:remaining_space] + "...")
                break
        
        return "\n\n".join(context_parts)
    
    def get_full_context(self) -> str:
        """
        Get the full document text.
        
        Returns:
            str: The complete document content.
        """
        return self._full_text
    
    def is_futuruma_related(self, query: str) -> bool:
        """
        Check if a query is related to Futuruma event.
        
        Args:
            query: The user's query.
        
        Returns:
            bool: True if query is Futuruma-related, False otherwise.
        """
        query_lower = query.lower()
        
        futuruma_keywords = [
            'futuruma', 'future-rama', 'event', 'tech fest', 'nepal', 'project', 'robotics',
            'ai', 'artificial intelligence', 'cybersecurity', 'venue', 'city',
            'ing skill academy', 'skill museum', 'smarc', 's-mark', 'organizer',
            'dermascan', 'derma scan', 'laser tag', 'cybercentric', 'maths assistant',
            'showcase', 'exhibition'
        ]
        
        return any(keyword in query_lower for keyword in futuruma_keywords)
    
    def get_section(self, section_name: str) -> Optional[str]:
        """
        Get a specific section by name.
        
        Args:
            section_name: Name of the section to retrieve.
        
        Returns:
            Optional[str]: Section content or None if not found.
        """
        section_name_lower = section_name.lower()
        
        for key, value in self._document_sections.items():
            if section_name_lower in key or key in section_name_lower:
                return value
        
        return None
    
    def list_sections(self) -> List[str]:
        """
        Get list of all section names.
        
        Returns:
            List[str]: List of section names.
        """
        return list(self._document_sections.keys())
    
    @property
    def source_file(self) -> Path:
        """
        Get the source file path.
        
        Returns:
            Path: Path to source file.
        """
        return self._source_file


def main() -> None:
    """
    Main function for testing RAG handler.
    """
    rag = RAGHandler()
    
    print(f"RAG Handler initialized")
    print(f"Source file: {rag.source_file}")
    print(f"\nAvailable sections: {rag.list_sections()}")
    
    # Test queries
    test_queries = [
        "What is Futuruma?",
        "Tell me about the AI projects",
        "Where is the event happening?",
        "What's the weather like?"  # Non-Futuruma query
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Is Futuruma-related: {rag.is_futuruma_related(query)}")
        
        context = rag.search_context(query)
        if context:
            print(f"\nRelevant context ({len(context)} chars):")
            print(context[:300] + "..." if len(context) > 300 else context)
        else:
            print("\nNo relevant context found")


if __name__ == '__main__':
    main()
