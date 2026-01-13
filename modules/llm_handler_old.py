"""
LLM Handler module for VoiceBox project.
Manages interaction with Ollama LLM using singleton pattern with RAG support.
"""

import ollama
from typing import Optional, Dict, Any, List
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
    Manages model initialization and response generation.
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
        self._initialized = True
        
        # Verify model is available
        self._verify_model()
        
        # Initialize RAG handler
        self._init_rag()
    
    def _init_rag(self) -> None:
        """
        Initialize the RAG handler.
        """
        try:
            # Use vector RAG if configured for FAISS search
            if Config.RAG_SEARCH_METHOD.lower() == "faiss":
                from modules.vector_rag_handler import VectorRAGHandler
                self._rag_handler = VectorRAGHandler()
                logger.info(f"Vector RAG handler initialized (FAISS + {Config.RAG_EMBEDDING_MODEL})")
            else:
                # Fall back to keyword-based RAG
                from modules.rag_handler import RAGHandler
                self._rag_handler = RAGHandler()
                logger.info("RAG handler initialized (keyword-based)")
        except Exception as e:
            logger.warning(f"Could not initialize RAG handler: {e}")
            # Try fallback to keyword RAG
            try:
                from modules.rag_handler import RAGHandler
                self._rag_handler = RAGHandler()
                logger.info("Fallback: Using keyword-based RAG")
            except Exception as fallback_e:
                logger.error(f"Failed to initialize both RAG handlers: {fallback_e}", exc_info=True)
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
    ) -> str:
        """
        Generate a response from the LLM with RAG support.
        
        Args:
            user_input: The user's input text.
            conversation_history: Optional conversation history for context.
        
        Returns:
            str: The generated response text.
        """
        try:
            # Check if RAG context is needed
            rag_context = ""
            if self._rag_handler and self._rag_handler.is_futuruma_related(user_input):
                logger.debug(f"Query is Futuruma-related, retrieving context")
                rag_context = self._rag_handler.search_context(user_input)
                if rag_context:
                    logger.info(f"RAG: Retrieved {len(rag_context)} chars of context")
                else:
                    logger.debug("RAG: No relevant context found for query")
            
            # Build system prompt with RAG context if available
            system_prompt = self._system_prompt
            if rag_context:
                system_prompt = f"""{self._system_prompt}

### IMPORTANT: Use ONLY the following verified information about Futuruma:

{rag_context}

CRITICAL INSTRUCTIONS:
- When answering about Futuruma, use ONLY the information provided above
- Futuruma is NOT an animated series - it is a tech fest in Nepal
- Do NOT make up or assume information that is not in the provided context
- If asked about something not covered in the context, say you don't have that specific information
- Keep responses brief, conversational, and easy to speak aloud
"""
            
            # Build messages
            messages: list[Dict[str, str]] = [
                {'role': 'system', 'content': system_prompt}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user input
            messages.append({'role': 'user', 'content': user_input})
            
            # Generate response
            response: Dict[str, Any] = ollama.chat(
                model=self._model_name,
                messages=messages,
                options={
                    'temperature': self._temperature,
                    'num_predict': self._max_length
                }
            )
            
            # Extract response text
            response_text: str = response['message']['content']
            logger.debug(f"Generated response ({len(response_text)} chars)")
            return response_text.strip()
            
        except Exception as e:
            error_message: str = f"Error generating LLM response: {e}"
            logger.error(error_message, exc_info=True)
            return "I apologize, but I'm having trouble generating a response right now."
    
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


def main() -> None:
    """
    Main function for testing LLM handler.
    """
    llm: LLMHandler = LLMHandler()
    print(f"LLM Handler initialized with model: {llm.model_name}")
    
    # Test response generation
    test_input: str = "Hello, how are you?"
    print(f"\nTest input: {test_input}")
    response: str = llm.generate_response(test_input)
    print(f"Response: {response}")


if __name__ == '__main__':
    main()
