"""
Search Handler module for VoiceBox project.
Factory module that returns the appropriate search handler based on configuration.
Supports both heuristic (keyword-based) and intent-based (LLM) search strategies.
"""

import sys
from pathlib import Path
from typing import Union

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config
from config.logger import get_logger

logger = get_logger('search')


def get_search_handler() -> Union['HeuristicSearchHandler', 'IntentSearchHandler']:
    """
    Factory function to get the appropriate search handler based on configuration.
    
    Returns:
        SearchHandler: Either HeuristicSearchHandler or IntentSearchHandler based on Config.SEARCH_HANDLER_TYPE
    """
    handler_type = Config.SEARCH_HANDLER_TYPE.lower()
    
    if handler_type == "intent":
        try:
            from modules.intent_search_handler import IntentSearchHandler
            logger.info("Using intent-based search handler (LLM classification)")
            return IntentSearchHandler()
        except ImportError as e:
            logger.warning(f"Failed to load intent search handler: {e}")
            logger.info("Falling back to heuristic search handler")
            from modules.heuristic_search_handler import HeuristicSearchHandler
            return HeuristicSearchHandler()
    
    elif handler_type == "heuristic":
        from modules.heuristic_search_handler import HeuristicSearchHandler
        logger.info("Using heuristic search handler (keyword-based)")
        return HeuristicSearchHandler()
    
    else:
        logger.warning(f"Unknown search handler type: {handler_type}. Using intent-based.")
        from modules.intent_search_handler import IntentSearchHandler
        return IntentSearchHandler()


# For backward compatibility, provide SearchHandler alias
SearchHandler = get_search_handler


def main() -> None:
    """
    Main function for testing search handler selection.
    """
    print(f"Configured search handler type: {Config.SEARCH_HANDLER_TYPE}")
    print("="*60)
    
    # Get handler based on configuration
    handler = get_search_handler()
    
    handler_name = handler.__class__.__name__
    print(f"\nActive handler: {handler_name}")
    print(f"Search enabled: {handler.is_enabled}")
    
    if hasattr(handler, 'has_llm'):
        print(f"LLM available: {handler.has_llm}")
    
    if handler.is_enabled:
        # Test query
        test_query = "What is the current stock price of Apple?"
        print(f"\nTest query: {test_query}")
        needs_search = handler.needs_search(test_query)
        print(f"Needs search: {needs_search}")
        
        if needs_search:
            print("\nPerforming search...")
            context, attrs = handler.search(test_query, max_results=2)
            if context:
                print(f"Context preview: {context[:300]}...")
                print(f"Found {len(attrs)} sources")
    else:
        print("\nSearch is disabled. Set TAVILY_API_KEY in .env to enable.")
    
    print("\n" + "="*60)
    print("Configuration Guide:")
    print("  - Set SEARCH_HANDLER_TYPE='intent' in config.py for LLM-based intent classification")
    print("  - Set SEARCH_HANDLER_TYPE='heuristic' in config.py for keyword-based matching")
    print("="*60)


if __name__ == '__main__':
    main()



if __name__ == '__main__':
    main()
