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
    LLM_MODEL: str = "gemma3:270m"
    OLLAMA_HOST: str = "http://localhost:11434"
    
    # TTS settings (MeloTTS)
    TTS_LANGUAGE: str = "EN"  # Language code for MeloTTS
    TTS_SPEAKER: str = "EN_INDIA"  # Speaker accent (EN-US, EN-BR, EN_INDIA, EN-AU, EN-Default)
    TTS_SPEED: float = 1.0  # Speech speed (adjustable)
    TTS_DEVICE: str = "auto"  # Device: 'auto', 'cpu', 'cuda', 'cuda:0', 'mps'
    TTS_SAMPLE_RATE: int = 44100  # MeloTTS sample rate
    
    # STT settings
    STT_MODEL_SIZE: str = "small"
    STT_DEVICE: str = "cuda"
    STT_COMPUTE_TYPE: str = "float16"
    STT_BEAM_SIZE: int = 5
    STT_VAD_FILTER: bool = True
    
    # LLM generation settings
    MAX_RESPONSE_LENGTH: int = 200
    TEMPERATURE: float = 0.1
    
    # RAG settings
    RAG_TOP_K: int = 2  # Number of top sections to retrieve
    RAG_MIN_SCORE: float = 0.7  # Minimum score threshold for retrieval (deprecated for vector search)
    RAG_SCORE_THRESHOLD: float = 0.85  # Cosine similarity threshold (0.0 to 1.0)
    RAG_MAX_CONTEXT_LENGTH: int = 1000  # Maximum context length in characters
    RAG_KEYWORD_BOOST: float = 5.0  # Score boost for section name matches (deprecated)
    RAG_SEARCH_METHOD: str = "semantic"  # Search method: 'keyword', 'faiss', 'semantic'
    RAG_CONTEXT_PRIORITY: bool = True  # Prioritize RAG context over general knowledge
    
    # Vector embeddings settings for RAG
    RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # sentence-transformers model
    RAG_VECTOR_DIMENSION: int = 384  # Embedding dimension (384 for MiniLM, 768 for larger models)
    RAG_CHUNK_SIZE: int = 100  # Target chunk size in characters for semantic chunking
    RAG_CHUNK_OVERLAP: int = 50  # Overlap between chunks in characters
    RAG_FAISS_INDEX_TYPE: str = "IVF"  # FAISS index type: 'Flat' (exact), 'IVF', 'HNSW'
    RAG_SIMILARITY_METRIC: str = "dot"  # Similarity metric: 'cosine', 'euclidean', 'dot'
    
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
