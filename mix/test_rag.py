#!/usr/bin/env python3
"""
Test script for VoiceBox RAG functionality.
Tests the integration of RAG with LLM for Futuruma queries.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from modules.llm_handler import LLMHandler
from modules.conversation_manager import ConversationManager

def test_rag_queries():
    """Test RAG-enhanced LLM responses."""
    
    print("="*60)
    print("Testing VoiceBox RAG Integration")
    print("="*60)
    
    # Initialize components
    llm = LLMHandler()
    conversation = ConversationManager()
    
    # Test queries
    test_queries = [
        "What is Futuruma?",
        "Tell me about the AI projects being showcased",
        "Which cities will host the event?",
        "What robotics projects are there?",
        "Who organized Futuruma?",
        "Tell me about DermaScan project",
    ]
    
    print(f"\nSession ID: {conversation.session_id}\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'-'*60}")
        print(f"Query {i}: {query}")
        print(f"{'-'*60}")
        
        # Add to history
        conversation.add_user_message(query)
        
        # Get response
        response = llm.generate_response(query, conversation.get_conversation_history(max_messages=10))
        
        # Add response to history
        conversation.add_assistant_message(response)
        
        # Log interaction
        conversation.log_interaction(
            user_query=query,
            model_response=response,
            response_time=0.5,
            status="success"
        )
        
        print(f"Response: {response}")
    
    # Save conversation
    print(f"\n{'='*60}")
    saved_path = conversation.save_conversation()
    
    # Show statistics
    stats = conversation.get_statistics()
    print("\nSession Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n{'='*60}")
    print("Test completed successfully!")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    test_rag_queries()
