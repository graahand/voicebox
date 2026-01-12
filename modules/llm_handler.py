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
                print(f"Vector RAG handler initialized (FAISS + {Config.RAG_EMBEDDING_MODEL})")
            else:
                # Fall back to keyword-based RAG
                from modules.rag_handler import RAGHandler
                self._rag_handler = RAGHandler()
                print("RAG handler initialized successfully (keyword-based)")
        except Exception as e:
            print(f"Warning: Could not initialize RAG handler: {e}")
            # Try fallback to keyword RAG
            try:
                from modules.rag_handler import RAGHandler
                self._rag_handler = RAGHandler()
                print("Fallback: Using keyword-based RAG")
            except:
                self._rag_handler = None
    
    def _verify_model(self) -> None:
        """
        Verify that the specified model is available in Ollama.
        """
        try:
            response = ollama.list()
            available_models: list[str] = [model.model for model in response.models]
            
            if self._model_name not in available_models:
                print(f"Warning: Model {self._model_name} not found. Available models: {available_models}")
                print(f"Please run: ollama pull {self._model_name}")
        except Exception as e:
            print(f"Error verifying model: {e}")
    
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
                rag_context = self._rag_handler.search_context(user_input)
                if rag_context:
                    print("RAG: Using Futuruma knowledge base")
            
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
            return response_text.strip()
            
        except Exception as e:
            error_message: str = f"Error generating LLM response: {e}"
            print(error_message)
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
