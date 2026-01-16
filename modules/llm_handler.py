"""
LLM Handler module for VoiceBox project.
Manages interaction with Ollama LLM using singleton pattern with LangChain RAG support.
Includes real-time search integration via Tavily.
"""

import ollama
from ollama import chat
from typing import Optional, Dict, Any, List, Tuple
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config
from config.logger import get_logger, suppress_library_warnings

# Suppress third-party library warnings
suppress_library_warnings()

logger = get_logger('llm')


class LLMHandler:
    """
    Singleton class for handling LLM operations with Ollama.
    Manages model initialization and response generation with LangChain RAG.
    """
    
    _instance: Optional['LLMHandler'] = None
    
    def __new__(cls) -> 'LLMHandler':
        """
        Implement singleton pattern.
        
        Returns:
            LLMHandler: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """
        Initialize LLM handler.
        Only runs once due to singleton pattern.
        """
        if self._initialized:
            return
        
        self._model_name: str = Config.LLM_MODEL
        self._system_prompt: str = Config.load_system_prompt()
        self._max_length: int = Config.MAX_RESPONSE_LENGTH
        self._temperature: float = Config.TEMPERATURE
        self._rag_handler = None
        self._search_handler = None
        self._search_enabled: bool = True
        self._rag_enabled: bool = True
        self._initialized = True
        
        # Verify model is available
        self._verify_model()
        
        # Initialize RAG handler
        self._init_rag()
        
        # Initialize Search handler
        self._init_search()
    
    def _init_search(self) -> None:
        """
        Initialize the Tavily search handler.
        """
        try:
            from modules.search_handler import SearchHandler
            self._search_handler = SearchHandler()
            
            if self._search_handler.is_enabled:
                logger.info("Search handler initialized successfully")
            else:
                logger.warning("Search handler initialized but not enabled (check API key)")
                
        except ImportError as e:
            logger.warning(f"Could not import search handler: {e}")
            self._search_handler = None
        except Exception as e:
            logger.error(f"Failed to initialize search handler: {e}", exc_info=True)
            self._search_handler = None
    
    def _init_rag(self) -> None:
        """
        Initialize the LangChain RAG handler.
        """
        try:
            from modules.langchain_rag_handler import LangChainRAGHandler
            self._rag_handler = LangChainRAGHandler()
            
            if self._rag_handler.is_ready:
                logger.info("LangChain RAG handler initialized successfully")
            else:
                logger.warning("LangChain RAG handler initialized but not ready")
                self._rag_handler = None
                
        except ImportError as e:
            logger.warning(f"Could not import LangChain RAG: {e}")
            logger.warning("Install with: pip install langchain langchain-community chromadb")
            self._rag_handler = None
        except Exception as e:
            logger.error(f"Failed to initialize RAG handler: {e}", exc_info=True)
            self._rag_handler = None
    
    def _verify_model(self) -> None:
        """
        Verify that the specified model is available in Ollama.
        """
        try:
            response = ollama.list()
            available_models: list[str] = [model.model for model in response.models]
            
            logger.info(f"Checking for model: {self._model_name}")
            logger.debug(f"Available models: {available_models}")
            
            if self._model_name not in available_models:
                logger.warning(f"Model {self._model_name} not found in available models")
                logger.warning(f"Available models: {', '.join(available_models)}")
                logger.warning(f"To install, run: ollama pull {self._model_name}")
            else:
                logger.info(f"Model {self._model_name} verified successfully")
        except Exception as e:
            logger.error(f"Error verifying model: {e}", exc_info=True)
    
    def generate_response(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate a response from the LLM with RAG and search support.
        
        Args:
            user_input: The user's input text.
            conversation_history: Optional conversation history for context.
        
        Returns:
            Tuple of (response_text, source_attributions)
        """
        try:
            rag_context = ""
            search_context = ""
            attributions = []
            
            # Check if search is needed for real-time information
            if self._search_enabled and self._search_handler and self._search_handler.is_enabled:
                if self._search_handler.needs_search(user_input):
                    logger.info(f"Query requires search: {user_input}")
                    search_context, search_attrs = self._search_handler.search(user_input)
                    if search_context:
                        logger.info(f"Search: Retrieved {len(search_context)} chars from web")
                        # Add search attributions with type marker
                        for attr in search_attrs:
                            attr['type'] = 'web_search'
                        attributions.extend(search_attrs)
            
            # Get RAG context (local knowledge base)
            if self._rag_enabled and self._rag_handler:
                logger.debug(f"Retrieving RAG context for: {user_input}")
                rag_context, rag_attrs = self._rag_handler.search_context(user_input)
                
                if rag_context:
                    logger.info(f"RAG: Retrieved {len(rag_context)} chars from {len(rag_attrs)} sources")
                    # Add RAG attributions with type marker
                    for attr in rag_attrs:
                        attr['type'] = 'local_knowledge'
                    attributions.extend(rag_attrs)
                else:
                    logger.debug("RAG: No relevant context found for query")
            
            # Build system prompt with context
            system_prompt = self._system_prompt
            
            # Combine contexts
            combined_context = ""
            if search_context:
                combined_context += f"\n[REAL-TIME WEB INFORMATION]\n{search_context}\n"
            if rag_context:
                combined_context += f"\n[LOCAL KNOWLEDGE BASE]\n{rag_context}\n"
            
            if combined_context:
                system_prompt = f"""{self._system_prompt}

IMPORTANT: Use the following information to answer questions:
{combined_context}

INSTRUCTIONS:
- Answer the user's question directly using the information above
- For real-time data (stocks, weather, news), prioritize web search results
- Do NOT start with greetings if the user asked a specific question
- Keep responses brief, conversational, and easy to speak aloud
- If the information above does not contain the answer, say you do not have that information
"""
            
            # Build messages
            messages: list[Dict[str, str]] = [
                {'role': 'system', 'content': system_prompt}
            ]
            
            # Add conversation history if provided (but limit to avoid confusion)
            if conversation_history and len(conversation_history) > 0:
                # Only use last 4 messages to avoid context confusion
                recent_history = conversation_history[-4:]
                messages.extend(recent_history)
            
            # Add current user input
            messages.append({'role': 'user', 'content': user_input})
            
            # Check if model supports thinking
            supports_thinking = Config.ENABLE_THINKING and any(
                self._model_name.startswith(model) for model in Config.THINKING_MODELS
            )
            
            # Generate response
            if supports_thinking:
                logger.info(f"Using thinking mode for model: {self._model_name}")
                response = chat(self._model_name, messages=messages, think=False)
                
                # Extract thinking and response
                thinking_process = getattr(response.message, 'thinking', '')
                response_text = response.message.content
                
                if thinking_process:
                    logger.info(f"Thinking process ({len(thinking_process)} chars)")
                    logger.debug(f"Thinking: {thinking_process[:200]}...")
                    # Add thinking to response for display (optional)
                    # Uncomment to include thinking in conversation
                    # response_text = f"[Thinking: {thinking_process}]\n\n{response_text}"
            else:
                response: Dict[str, Any] = ollama.chat(
                    model=self._model_name,
                    messages=messages,
                    options={
                        'temperature': self._temperature,
                        'num_predict': self._max_length
                    }, 
                    think=False
                )
                response_text: str = response['message']['content']
            
            logger.debug(f"Generated response ({len(response_text)} chars)")
            
            return response_text.strip(), attributions
            
        except Exception as e:
            error_message: str = f"Error generating LLM response: {e}"
            logger.error(error_message, exc_info=True)
            return "I apologize, but I'm having trouble generating a response right now.", []
    
    def get_source_attribution_text(self, attributions: List[Dict[str, Any]]) -> str:
        """
        Get formatted source attribution text.
        Handles both RAG attributions (section, score) and search attributions (title, url).
        
        Args:
            attributions: List of source attributions from RAG or search.
        
        Returns:
            Formatted attribution string.
        """
        if not attributions:
            return ""
        
        # Detect attribution type by checking first item keys
        first_attr = attributions[0]
        
        # RAG attributions have 'section' key
        if 'section' in first_attr:
            if self._rag_handler:
                return self._rag_handler.get_source_attribution_text(attributions)
            return ""
        
        # Search attributions have 'title' and 'url' keys
        elif 'title' in first_attr:
            lines = ["Information retrieved from web:"]
            for i, attr in enumerate(attributions, 1):
                title = attr.get('title', 'Unknown')
                url = attr.get('url', '')
                lines.append(f"  {i}. {title}")
                if url:
                    lines.append(f"     {url}")
            return "\n".join(lines)
        
        return ""
    
    @property
    def model_name(self) -> str:
        """
        Get the model name.
        
        Returns:
            str: The model name.
        """
        return self._model_name
    
    @property
    def system_prompt(self) -> str:
        """
        Get the system prompt.
        
        Returns:
            str: The system prompt.
        """
        return self._system_prompt
    
    @property
    def rag_enabled(self) -> bool:
        """Check if RAG is enabled and ready."""
        return self._rag_enabled and self._rag_handler is not None and self._rag_handler.is_ready
    
    @property
    def search_enabled(self) -> bool:
        """Check if search is enabled and ready."""
        return self._search_enabled and self._search_handler is not None and self._search_handler.is_enabled
    
    def set_rag_enabled(self, enabled: bool) -> None:
        """Enable or disable RAG."""
        self._rag_enabled = enabled
        logger.info(f"RAG {'enabled' if enabled else 'disabled'}")
    
    def set_search_enabled(self, enabled: bool) -> None:
        """Enable or disable search."""
        self._search_enabled = enabled
        logger.info(f"Search {'enabled' if enabled else 'disabled'}")


def main() -> None:
    """
    Main function for testing LLM handler.
    """
    llm: LLMHandler = LLMHandler()
    print(f"LLM Handler initialized with model: {llm.model_name}")
    print(f"RAG enabled: {llm.rag_enabled}")
    
    # Test response generation
    test_input: str = "What is laser tag project?"
    print(f"\nTest input: {test_input}")
    response, attributions = llm.generate_response(test_input)
    print(f"Response: {response}")
    
    if attributions:
        print(f"\nSources:")
        print(llm.get_source_attribution_text(attributions))


if __name__ == '__main__':
    main()
