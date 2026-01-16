"""
Heuristic Search Handler module for VoiceBox project.
Provides real-time web search using keyword-based heuristics for intent detection.
"""

import os
import re
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config
from config.logger import get_logger, suppress_library_warnings

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Config.BASE_DIR / ".env")
except ImportError:
    pass

suppress_library_warnings()

logger = get_logger('search')


class HeuristicSearchHandler:
    """
    Singleton class for handling web searches using keyword-based heuristics.
    Provides real-time information for queries requiring current data.
    """
    
    _instance: Optional['HeuristicSearchHandler'] = None
    
    # Keywords that trigger search
    SEARCH_TRIGGERS = [
        # Financial
        'stock', 'stocks', 'share price', 'market', 'bitcoin', 'crypto', 'cryptocurrency',
        'nasdaq', 'dow jones', 's&p', 'nifty', 'sensex', 'trading', 'nepse'
        # Weather
        'weather', 'temperature', 'forecast', 'rain', 'snow', 'climate',
        # Current events
        'news', 'latest', 'recent', 'today', 'yesterday', 'this week', 'current',
        'happening', 'breaking',
        # People & Net worth
        'net worth', 'networth', 'richest', 'billionaire', 'ceo of', 'founder of',
        'who is the current', 'who won', 'election',
        # Sports
        'score', 'match', 'game result', 'tournament', 'championship', 'world cup',
        'olympics', 'premier league', 'ipl', 'nba', 'nfl',
        # Politics
        'president', 'prime minister', 'government', 'political', 'election',
        'vote', 'congress', 'parliament',
        # Technology
        'release date', 'launch', 'new iphone', 'new android', 'upcoming',
        # General current info
        'how much is', 'what is the price', 'cost of', 'value of',
        'population of', 'gdp of', 'capital of',
        # Time-sensitive
        'right now', 'at the moment', 'currently', 'as of today',
    ]
    
    def __new__(cls) -> 'HeuristicSearchHandler':
        """
        Implement singleton pattern.
        
        Returns:
            HeuristicSearchHandler: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """
        Initialize search handler.
        Only runs once due to singleton pattern.
        """
        if self._initialized:
            return
        
        self._api_key: Optional[str] = os.getenv('TAVILY_API_KEY')
        self._client = None
        self._enabled: bool = False
        self._initialized = True
        
        # Initialize the client
        self._init_client()
    
    def _init_client(self) -> None:
        """
        Initialize the Tavily client.
        """
        if not self._api_key or self._api_key == 'your_tavily_api_key_here':
            logger.warning("Tavily API key not configured. Search disabled.")
            logger.info("Set TAVILY_API_KEY in .env file to enable search.")
            self._enabled = False
            return
        
        try:
            from tavily import TavilyClient
            
            self._client = TavilyClient(api_key=self._api_key)
            self._enabled = True
            logger.info("Tavily search client initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Tavily not installed: {e}")
            logger.info("Install with: pip install tavily-python")
            self._enabled = False
        except Exception as e:
            logger.error(f"Error initializing Tavily client: {e}", exc_info=True)
            self._enabled = False
    
    def needs_search(self, query: str) -> bool:
        """
        Determine if a query requires real-time search.
        
        Args:
            query: The user's query.
        
        Returns:
            bool: True if search is needed.
        """
        if not self._enabled:
            return False
        
        query_lower = query.lower()
        
        # Check for trigger keywords
        for trigger in self.SEARCH_TRIGGERS:
            if trigger in query_lower:
                logger.debug(f"Search triggered by keyword: '{trigger}'")
                return True
        
        # Check for question patterns about current info
        current_patterns = [
            r'\bwhat is .+ (price|worth|value|cost)\b',
            r'\bhow much (is|does|are)\b',
            r'\bwho (is|are) the current\b',
            r'\bwhat happened\b',
            r'\bwhen (is|was|will)\b',
            r'\bwhere (is|are)\b.+(now|today|currently)',
        ]
        
        for pattern in current_patterns:
            if re.search(pattern, query_lower):
                logger.debug(f"Search triggered by pattern: '{pattern}'")
                return True
        
        return False
    
    def search(
        self,
        query: str,
        max_results: int = 3,
        search_depth: str = "basic"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Perform a web search using Tavily.
        
        Args:
            query: The search query.
            max_results: Maximum number of results to return.
            search_depth: Search depth ("basic" or "advanced").
        
        Returns:
            Tuple[str, List[Dict]]: (formatted_context, raw_results)
        """
        if not self._enabled or not self._client:
            logger.warning("Search not available - client not initialized")
            return "", []
        
        try:
            logger.info(f"Searching for: {query}")
            
            # Perform search
            response = self._client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=True,
                include_raw_content=False
            )
            
            # Extract results
            results = response.get('results', [])
            answer = response.get('answer', '')
            
            logger.info(f"Search returned {len(results)} results")
            
            # Format context for LLM
            context_parts = []
            
            if answer:
                context_parts.append(f"Summary: {answer}")
            
            # Add currency context hint if query is about stocks/prices
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in ['stock', 'price', 'nepse', 'share']):
                context_parts.append("\n[Currency Context: Use NPR for NEPSE/Nepal stocks, INR for Indian stocks, USD for US stocks]\n")
            
            # Add currency context hint if query is about stocks/prices
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in ['stock', 'price', 'nepse', 'share']):
                context_parts.append("\n[Currency Context: Use NPR for NEPSE/Nepal stocks, INR for Indian stocks, USD for US stocks]\n")
            
            for i, result in enumerate(results[:max_results], 1):
                title = result.get('title', 'Unknown')
                content = result.get('content', '')
                url = result.get('url', '')
                
                # Truncate long content
                if len(content) > 500:
                    content = content[:500] + "..."
                
                context_parts.append(f"\n[Source {i}: {title}]\n{content}")
            
            context = "\n".join(context_parts)
            
            # Prepare attribution info
            attributions = [
                {
                    'title': r.get('title', 'Unknown'),
                    'url': r.get('url', ''),
                    'snippet': r.get('content', '')[:200] + '...' if len(r.get('content', '')) > 200 else r.get('content', '')
                }
                for r in results[:max_results]
            ]
            
            return context, attributions
            
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return "", []
    
    def get_search_context(self, query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Get search context if the query needs it.
        
        Args:
            query: The user's query.
        
        Returns:
            Tuple[str, List[Dict]]: (context, attributions) or ("", []) if not needed
        """
        if not self.needs_search(query):
            return "", []
        
        return self.search(query)
    
    @property
    def is_enabled(self) -> bool:
        """Check if search is enabled."""
        return self._enabled
    
    def enable(self) -> None:
        """Enable search (if API key is available)."""
        if self._api_key and self._api_key != 'your_tavily_api_key_here':
            self._init_client()
    
    def disable(self) -> None:
        """Disable search."""
        self._enabled = False


def main() -> None:
    """
    Main function for testing heuristic search handler.
    """
    search = HeuristicSearchHandler()
    print(f"Heuristic Search Handler")
    print(f"Search enabled: {search.is_enabled}")
    
    if search.is_enabled:
        # Test queries
        test_queries = [
            "What is the current stock price of Apple?",
            "Who is the richest person in the world right now?",
            "What's the weather like in New York today?",
            "What is the current price of nepse?",
            "Hello, how are you?",  # Should not trigger search
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            needs_search = search.needs_search(query)
            print(f"Needs search: {needs_search}")
            
            if needs_search:
                context, attrs = search.search(query)
                print(f"Context: {context[:200]}..." if context else "No results")
    else:
        print("Search is disabled. Set TAVILY_API_KEY in .env to enable.")


if __name__ == '__main__':
    main()
