"""
Conversation Manager module for VoiceBox project.
Manages conversation history, JSON logging, and timestamps.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config


class ConversationManager:
    """
    Manages conversation history and logging.
    Stores conversations in JSON format with timestamps and metadata.
    """
    
    def __init__(self, session_id: Optional[str] = None) -> None:
        """
        Initialize conversation manager.
        
        Args:
            session_id: Optional session identifier. If None, generates one from timestamp.
        """
        self._session_id: str = session_id or self._generate_session_id()
        self._conversation_history: List[Dict[str, str]] = []
        self._session_log: List[Dict[str, Any]] = []
        self._session_start: datetime = datetime.now()
        
        Config.ensure_directories()
    
    @staticmethod
    def _generate_session_id() -> str:
        """
        Generate a session ID from current timestamp.
        
        Returns:
            str: Session ID in format 'session_YYYYMMDD_HHMMSS'.
        """
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}"
    
    def add_user_message(self, message: str) -> None:
        """
        Add a user message to conversation history.
        
        Args:
            message: The user's message text.
        """
        self._conversation_history.append({
            'role': 'user',
            'content': message
        })
    
    def add_assistant_message(self, message: str) -> None:
        """
        Add an assistant message to conversation history.
        
        Args:
            message: The assistant's message text.
        """
        self._conversation_history.append({
            'role': 'assistant',
            'content': message
        })
    
    def log_interaction(
        self,
        user_query: str,
        model_response: str,
        response_time: float,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a complete interaction with metadata.
        
        Args:
            user_query: The user's query.
            model_response: The model's response.
            response_time: Time taken to generate response in seconds.
            status: Status of the interaction ('success' or 'error').
            metadata: Optional additional metadata.
        """
        interaction: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'user_query': user_query,
            'model_response': model_response,
            'response_time_seconds': round(response_time, 3),
            'status': status
        }
        
        if metadata:
            interaction['metadata'] = metadata
        
        self._session_log.append(interaction)
    
    def save_conversation(self, filename: Optional[str] = None) -> Path:
        """
        Save conversation history and logs to JSON file.
        
        Args:
            filename: Optional filename. If None, uses session_id.
        
        Returns:
            Path: Path to saved conversation file.
        """
        if filename is None:
            filename = f"{self._session_id}.json"
        
        output_path: Path = Config.CONVERSATIONS_DIR / filename
        
        session_data: Dict[str, Any] = {
            'session_id': self._session_id,
            'session_start': self._session_start.isoformat(),
            'session_end': datetime.now().isoformat(),
            'total_interactions': len(self._session_log),
            'conversation_history': self._conversation_history,
            'interaction_log': self._session_log
        }
        
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(session_data, file, indent=2, ensure_ascii=False)
        
        print(f"Conversation saved to: {output_path}")
        return output_path
    
    def load_conversation(self, filepath: Path) -> bool:
        """
        Load conversation from JSON file.
        
        Args:
            filepath: Path to conversation file.
        
        Returns:
            bool: True if loaded successfully, False otherwise.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                session_data: Dict[str, Any] = json.load(file)
            
            self._session_id = session_data.get('session_id', self._session_id)
            self._conversation_history = session_data.get('conversation_history', [])
            self._session_log = session_data.get('interaction_log', [])
            
            print(f"Conversation loaded from: {filepath}")
            return True
            
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return False
    
    def get_conversation_history(
        self,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get conversation history, optionally limited to recent messages.
        
        Args:
            max_messages: Maximum number of recent messages to return.
        
        Returns:
            List[Dict[str, str]]: Conversation history.
        """
        if max_messages is None:
            return self._conversation_history.copy()
        
        return self._conversation_history[-max_messages:]
    
    def clear_history(self) -> None:
        """
        Clear conversation history and logs.
        """
        self._conversation_history.clear()
        self._session_log.clear()
        print("Conversation history cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get conversation statistics.
        
        Returns:
            Dict[str, Any]: Statistics about the conversation.
        """
        total_interactions: int = len(self._session_log)
        
        if total_interactions == 0:
            return {
                'total_interactions': 0,
                'average_response_time': 0,
                'success_rate': 0
            }
        
        total_time: float = sum(
            log['response_time_seconds'] 
            for log in self._session_log
        )
        avg_time: float = total_time / total_interactions
        
        successful: int = sum(
            1 for log in self._session_log 
            if log.get('status') == 'success'
        )
        success_rate: float = (successful / total_interactions) * 100
        
        return {
            'session_id': self._session_id,
            'total_interactions': total_interactions,
            'average_response_time_seconds': round(avg_time, 3),
            'success_rate_percent': round(success_rate, 2),
            'session_duration_seconds': (datetime.now() - self._session_start).total_seconds()
        }
    
    @property
    def session_id(self) -> str:
        """
        Get the session ID.
        
        Returns:
            str: The session ID.
        """
        return self._session_id


def main() -> None:
    """
    Main function for testing conversation manager.
    """
    Config.ensure_directories()
    
    # Create manager
    manager: ConversationManager = ConversationManager()
    print(f"Conversation Manager initialized with session: {manager.session_id}")
    
    # Simulate some interactions
    manager.add_user_message("Hello, how are you?")
    manager.add_assistant_message("I'm doing well, thank you!")
    manager.log_interaction(
        user_query="Hello, how are you?",
        model_response="I'm doing well, thank you!",
        response_time=0.523,
        status="success"
    )
    
    manager.add_user_message("What's the weather like?")
    manager.add_assistant_message("I don't have access to real-time weather data.")
    manager.log_interaction(
        user_query="What's the weather like?",
        model_response="I don't have access to real-time weather data.",
        response_time=0.412,
        status="success"
    )
    
    # Get statistics
    stats: Dict[str, Any] = manager.get_statistics()
    print(f"\nConversation statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Save conversation
    saved_path: Path = manager.save_conversation()
    print(f"\nConversation saved to: {saved_path}")


if __name__ == '__main__':
    main()
