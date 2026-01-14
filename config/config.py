"""
Configuration module for VoiceBox project.
This module manages all configuration settings including paths, model settings, and system prompts.
"""

from pathlib import Path
from typing import Dict, Any


class Config:
    """
    Configuration class for VoiceBox project.
    Manages paths, model settings, and system configuration.
    """
    
    # Base paths
    BASE_DIR: Path = Path(__file__).parent.parent
    CONFIG_DIR: Path = BASE_DIR / "config"
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # Data subdirectories
    AUDIO_DIR: Path = DATA_DIR / "audio"
    CONVERSATIONS_DIR: Path = DATA_DIR / "conversations"
    
    # System prompt
    SYSTEM_PROMPT_PATH: Path = CONFIG_DIR / "system_prompt.txt"
    
    # Model settings
    LLM_MODEL: str = "qwen2:1.5b"
    OLLAMA_HOST: str = "http://localhost:11434"
    
    # TTS settings (PiperTTS)
    TTS_VOICE_MODEL: str = "en_US-lessac-medium"  # Piper voice model name
    TTS_VOICE_PATH: str = ""  # Path to .onnx voice file (auto-download if empty)
    TTS_SPEED: float = 1.0  # Speech speed (length_scale: higher = slower)
    TTS_VOLUME: float = 1.0  # Volume level (0.0 to 1.0)
    TTS_USE_CUDA: bool = True  # Use GPU acceleration if available
    TTS_SAMPLE_RATE: int = 22050  # PiperTTS sample rate
    
    # STT settings
    STT_MODEL_SIZE: str = "small"
    STT_DEVICE: str = "cuda"
    STT_COMPUTE_TYPE: str = "float16"
    STT_BEAM_SIZE: int = 5
    STT_VAD_FILTER: bool = True
    STT_CONFIDENCE_THRESHOLD: float = 0.5  # Minimum confidence for a transcription to be accepted (0.0 to 1.0)
    
    # LLM generation settings
    MAX_RESPONSE_LENGTH: int = 200
    TEMPERATURE: float = 0.5
    
    # RAG settings
    RAG_TOP_K: int = 5  # Number of top sections to retrieve
    RAG_MIN_SCORE: float = 0.7  # Minimum score threshold for retrieval (deprecated)
    RAG_SCORE_THRESHOLD: float = 0.7  # Similarity threshold (0.0 to 1.0, lower = more results)
    RAG_MAX_CONTEXT_LENGTH: int = 1500  # Maximum context length in characters
    RAG_KEYWORD_BOOST: float = 5.0  # Score boost for section name matches (deprecated)
    RAG_SEARCH_METHOD: str = "langchain"  # Search method: 'langchain' (recommended), 'faiss', 'keyword'
    RAG_CONTEXT_PRIORITY: bool = True  # Prioritize RAG context over general knowledge
    
    # Vector embeddings settings for RAG
    # Note: ibm-granite/granite-embedding-english-r2 has 8192 token limit
    RAG_EMBEDDING_MODEL: str = "ibm-granite/granite-embedding-english-r2"  # Granite model with 8192 token context
    RAG_VECTOR_DIMENSION: int = 768  # Embedding dimension (768 for Granite)
    RAG_CHUNK_SIZE: int = 1024  # Target chunk size in characters (larger for Granite)
    RAG_CHUNK_OVERLAP: int = 100  # Overlap between chunks in characters
    RAG_FAISS_INDEX_TYPE: str = "Flat"  # FAISS index type (deprecated, using ChromaDB)
    RAG_SIMILARITY_METRIC: str = "cosine"  # Similarity metric
    
    # Source data file
    RAG_SOURCE_FILE: str = "source_data_structured.md"  # Structured source data
    
    @classmethod
    def load_system_prompt(cls) -> str:
        """
        Load system prompt from file.
        
        Returns:
            str: The system prompt text.
        """
        try:
            with open(cls.SYSTEM_PROMPT_PATH, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except FileNotFoundError:
            default_prompt: str = (
                "You are a interactive talkbot which will be conversing with people in day to day life. "
                "You answer the queries of the users briefly and swiftly. "
                "The text you generates must be speak-able with tts without any obstruction. "
                "Remember you are developed by skill museum okay."
            )
            return default_prompt
    
    @classmethod
    def ensure_directories(cls) -> None:
        """
        Ensure all required directories exist.
        Creates directories if they don't exist.
        """
        directories: list[Path] = [
            cls.DATA_DIR,
            cls.LOGS_DIR,
            cls.AUDIO_DIR,
            cls.CONVERSATIONS_DIR,
            cls.CONFIG_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """
        Get configuration as a dictionary.
        
        Returns:
            Dict[str, Any]: Configuration dictionary.
        """
        return {
            'llm_model': cls.LLM_MODEL,
            'ollama_host': cls.OLLAMA_HOST,
            'tts_language': cls.TTS_LANGUAGE,
            'tts_speaker': cls.TTS_SPEAKER,
            'tts_speed': cls.TTS_SPEED,
            'tts_device': cls.TTS_DEVICE,
            'tts_sample_rate': cls.TTS_SAMPLE_RATE,
            'stt_model_size': cls.STT_MODEL_SIZE,
            'stt_device': cls.STT_DEVICE,
            'stt_compute_type': cls.STT_COMPUTE_TYPE,
            'max_response_length': cls.MAX_RESPONSE_LENGTH,
            'temperature': cls.TEMPERATURE
        }


if __name__ == '__main__':
    # Test configuration
    Config.ensure_directories()
    print("Configuration loaded successfully")
    print(f"Base directory: {Config.BASE_DIR}")
    print(f"System prompt: {Config.load_system_prompt()[:100]}...")
