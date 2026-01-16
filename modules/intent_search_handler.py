"""
Intent-Based Search Handler module for VoiceBox project.
Uses LLM-based intent classification to determine if web search is needed.
More robust than keyword-based heuristics.
"""

import os
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


class IntentSearchHandler:
    """
    Singleton class for handling web searches using LLM-based intent classification.
    Uses Ollama to determine if a query requires real-time information.
    """
    
    _instance: Optional['IntentSearchHandler'] = None
    
    # Intent classification prompt
    INTENT_PROMPT = """You are a search intent classifier. Analyze the user's query and determine if it requires real-time web search to answer accurately.

Queries that NEED search (return YES):
- Current events, news, or recent happenings
- Real-time data (stock prices, weather, scores, exchange rates)
- Net worth, wealth, or financial information about people/companies
- Political information (current leaders, election results)
- Product prices, availability, or release dates
- Sports scores, match results, tournament standings
- Population, GDP, or statistical data that changes
- Any query with time indicators (today, now, current, latest, recent)
- Questions about "who is the current..." or "what is the price of..."

Queries that DON'T NEED search (return NO):
- General knowledge questions (historical facts, definitions, concepts)
- Math problems or calculations
- Programming or technical how-to questions
- Conversational queries (greetings, small talk)
- Questions about established facts (who invented X, when was Y born)
- Requests for explanations or descriptions of known concepts
- Questions about the VoiceBox system itself or Futuruma event

Respond with ONLY "YES" or "NO".

User query: {query}

Does this query require real-time web search?"""
    
    def __new__(cls) -> 'IntentSearchHandler':
        """
        Implement singleton pattern.
        
        Returns:
            IntentSearchHandler: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """
        Initialize intent-based search handler.
        Only runs once due to singleton pattern.
        """
        if self._initialized:
            return
        
        self._api_key: Optional[str] = os.getenv('TAVILY_API_KEY')
        self._client = None
        self._enabled: bool = False
        self._ollama_available: bool = False
        self._initialized = True
        
        # Initialize components
        self._init_ollama()
        self._init_client()
    
    def _init_ollama(self) -> None:
        """
        Check if Ollama is available for intent classification.
        """
        try:
            import ollama
            
            # Try to list models to verify connection
            ollama.list()
            self._ollama_available = True
            logger.info("Ollama available for intent classification")
            
        except ImportError:
            logger.warning("Ollama not installed. Intent classification disabled.")
            self._ollama_available = False
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._ollama_available = False
    
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
        Use LLM to determine if a query requires real-time search.
        Falls back to basic heuristics if LLM is unavailable.
        
        Args:
            query: The user's query.
        
        Returns:
            bool: True if search is needed.
        """
        if not self._enabled:
            return False
        
        # Use LLM-based intent classification
        if self._ollama_available:
            return self._classify_intent_with_llm(query)
        else:
            # Fallback to basic heuristics
            logger.warning("Using fallback heuristics (LLM unavailable)")
            return self._fallback_heuristic(query)
    
    def _classify_intent_with_llm(self, query: str) -> bool:
        """
        Use LLM to classify search intent.
        
        Args:
            query: The user's query.
        
        Returns:
            bool: True if search is needed.
        """
        try:
            import ollama
            
            # Format prompt
            prompt = self.INTENT_PROMPT.format(query=query)
            
            # Get classification from LLM (use small, fast model)
            response = ollama.generate(
                model=Config.LLM_MODEL,
                prompt=prompt,
                options={
                    'temperature': 0.0,  # Deterministic
                    'num_predict': 10,   # Only need YES/NO
                }
            )
            
            # Extract response
            classification = response['response'].strip().upper()
            
            # Check for YES/NO
            needs_search = 'YES' in classification
            
            logger.info(f"Intent classification for '{query}': {'SEARCH' if needs_search else 'NO SEARCH'}")
            logger.debug(f"LLM response: {classification}")
            
            return needs_search
            
        except Exception as e:
            logger.error(f"Error in LLM intent classification: {e}", exc_info=True)
            # Fallback to heuristic
            return self._fallback_heuristic(query)
    
    def _fallback_heuristic(self, query: str) -> bool:
        """
        Fallback heuristic when LLM is unavailable.
        Simple keyword matching.
        
        Args:
            query: The user's query.
        
        Returns:
            bool: True if search is likely needed.
        """
        query_lower = query.lower()
        
        # Simple keyword triggers
        time_indicators = ['today', 'now', 'current', 'latest', 'recent', 'this week', 'yesterday']
        financial = ['stock', 'price', 'net worth', 'cost', 'bitcoin', 'market']
        realtime = ['weather', 'score', 'news', 'election', 'who won']
        
        for keyword in time_indicators + financial + realtime:
            if keyword in query_lower:
                logger.debug(f"Fallback: Search triggered by keyword '{keyword}'")
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
        Get search context if the query needs it (using LLM intent classification).
        
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
    
    @property
    def has_llm(self) -> bool:
        """Check if LLM is available for intent classification."""
        return self._ollama_available
    
    def enable(self) -> None:
        """Enable search (if API key is available)."""
        if self._api_key and self._api_key != 'your_tavily_api_key_here':
            self._init_client()
    
    def disable(self) -> None:
        """Disable search."""
        self._enabled = False


def main() -> None:
    """
    Main function for testing intent-based search handler.
    """
    search = IntentSearchHandler()
    print(f"Search enabled: {search.is_enabled}")
    print(f"LLM available: {search.has_llm}")
    
    if search.is_enabled:
        # Test queries
        test_queries = [
            "What is the current stock price of Apple?",
            "Who is the richest person in the world right now?",
            "What's the weather like in New York today?",
            "What is the current price of nepse?",
            "Hello, how are you?",  # Should not trigger search
            "What is quantum computing?",  # Should not trigger search
            "Tell me about Futuruma event",  # Should not trigger search
            "What is the score of today's cricket match?",  # Should trigger search
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            needs_search = search.needs_search(query)
            print(f"LLM Decision: {'SEARCH' if needs_search else 'NO SEARCH'}")
            
            if needs_search:
                context, attrs = search.search(query)
                print(f"Context: {context[:200]}..." if context else "No results")
                if attrs:
                    print(f"Sources: {len(attrs)} found")
    else:
        print("Search is disabled. Set TAVILY_API_KEY in .env to enable.")


if __name__ == '__main__':
    main()
