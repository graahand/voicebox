"""
LangChain RAG Handler module for VoiceBox project.
Implements semantic search using LangChain with ChromaDB for document retrieval.
Uses a better embedding model with larger context window.
"""

from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config
from config.logger import get_logger, suppress_library_warnings

# Suppress third-party library warnings
suppress_library_warnings()

logger = get_logger('langchain_rag')

# Create separate logger for RAG retrievals
import logging
rag_retrieval_logger = logging.getLogger('rag_retrieval')
rag_retrieval_logger.setLevel(logging.DEBUG)

# Create handler for RAG retrieval log file
rag_log_path = Config.LOGS_DIR / "rag_retrieval.log"
rag_file_handler = logging.FileHandler(rag_log_path, encoding='utf-8')
rag_file_handler.setLevel(logging.DEBUG)
rag_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
rag_file_handler.setFormatter(rag_formatter)
rag_retrieval_logger.addHandler(rag_file_handler)


class LangChainRAGHandler:
    """
    LangChain-based RAG handler using ChromaDB and HuggingFace embeddings.
    Uses BAAI/bge-base-en-v1.5 which has 512 token context (better than MiniLM's 256).
    """
    
    _instance: Optional['LangChainRAGHandler'] = None
    
    def __new__(cls) -> 'LangChainRAGHandler':
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, source_file: Optional[Path] = None) -> None:
        """
        Initialize LangChain RAG handler.
        
        Args:
            source_file: Path to source data file.
        """
        if self._initialized:
            return
        
        if source_file is None:
            # Use configured source file
            source_file = Config.DATA_DIR / Config.RAG_SOURCE_FILE
        
        self._source_file = source_file
        self._vectorstore = None
        self._embeddings = None
        self._documents: List[Any] = []
        self._initialized = True
        
        # Configuration
        self._top_k = Config.RAG_TOP_K
        self._score_threshold = Config.RAG_SCORE_THRESHOLD
        
        # Initialize the system
        self._init_components()
    
    def _init_components(self) -> None:
        """Initialize LangChain components: embeddings and vectorstore."""
        try:
            # Import LangChain components
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.vectorstores import Chroma
            from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
            # from langchain.schema import Document
            from langchain_core.documents import Document
            
            # Use BGE embeddings - better than MiniLM, supports 512 tokens
            # bge-base-en-v1.5 has 768 dimensions and 512 token context
            embedding_model = "ibm-granite/granite-embedding-english-r2"
            logger.info(f"Loading embedding model: {embedding_model}")
            
            self._embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cuda' if Config.STT_DEVICE == 'cuda' else 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("Embedding model loaded successfully")
            
            # Load and process document
            if not self._source_file.exists():
                logger.warning(f"Source file not found: {self._source_file}")
                return
            
            with open(self._source_file, 'r', encoding='utf-8') as file:
                content = file.read()
            
            logger.info(f"Loaded document from {self._source_file} ({len(content)} chars)")
            
            # Split by markdown headers first
            headers_to_split = [
                ("#", "main_topic"),
                ("##", "section"),
                ("###", "subsection"),
            ]
            
            md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split)
            md_docs = md_splitter.split_text(content)
            
            # Further split long sections with recursive splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=400,  # Larger chunks since we have 512 token context
                chunk_overlap=50,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            self._documents = []
            for i, doc in enumerate(md_docs):
                # Create metadata with source information
                metadata = {
                    'source': str(self._source_file.name),
                    'doc_index': i,
                    **doc.metadata
                }
                
                # Get the section path for attribution
                section_path = []
                if 'main_topic' in doc.metadata:
                    section_path.append(doc.metadata['main_topic'])
                if 'section' in doc.metadata:
                    section_path.append(doc.metadata['section'])
                if 'subsection' in doc.metadata:
                    section_path.append(doc.metadata['subsection'])
                
                metadata['section_path'] = ' > '.join(section_path) if section_path else 'Introduction'
                
                # Split if too long
                if len(doc.page_content) > 400:
                    sub_docs = text_splitter.split_text(doc.page_content)
                    for j, sub_content in enumerate(sub_docs):
                        sub_metadata = {**metadata, 'chunk_index': j}
                        self._documents.append(Document(
                            page_content=sub_content,
                            metadata=sub_metadata
                        ))
                else:
                    metadata['chunk_index'] = 0
                    self._documents.append(Document(
                        page_content=doc.page_content,
                        metadata=metadata
                    ))
            
            logger.info(f"Created {len(self._documents)} document chunks")
            
            # Log sample chunks for debugging
            for i, doc in enumerate(self._documents[:3]):
                logger.debug(f"Sample chunk {i}: section={doc.metadata.get('section_path', 'N/A')}, "
                           f"content={doc.page_content[:100]}...")
            
            # Create ChromaDB vectorstore
            persist_directory = str(Config.DATA_DIR / "chroma_db")
            
            self._vectorstore = Chroma.from_documents(
                documents=self._documents,
                embedding=self._embeddings,
                persist_directory=persist_directory,
                collection_name="voicebox_rag"
            )
            
            logger.info(f"ChromaDB vectorstore created at {persist_directory}")
            
        except ImportError as e:
            logger.error(f"Missing LangChain dependencies: {e}")
            logger.error("Install with: pip install langchain langchain-community chromadb")
            self._vectorstore = None
        except Exception as e:
            logger.error(f"Error initializing LangChain RAG: {e}", exc_info=True)
            self._vectorstore = None
    
    def search_context(self, query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Search for relevant context using semantic similarity.
        
        Args:
            query: The user query.
        
        Returns:
            Tuple of (context_string, list of source attributions)
        """
        if self._vectorstore is None:
            logger.warning("Vectorstore not initialized, cannot search")
            return "", []
        
        try:
            # Perform similarity search with scores
            results = self._vectorstore.similarity_search_with_relevance_scores(
                query,
                k=self._top_k
            )
            
            if not results:
                logger.debug(f"No results found for query: {query}")
                rag_retrieval_logger.info(f"QUERY: {query}")
                rag_retrieval_logger.info("RESULTS: None found")
                return "", []
            
            # Filter by score threshold
            filtered_results = [
                (doc, score) for doc, score in results
                if score >= self._score_threshold
            ]
            
            if not filtered_results:
                logger.debug(f"No results above threshold {self._score_threshold}")
                rag_retrieval_logger.info(f"QUERY: {query}")
                rag_retrieval_logger.info(f"RESULTS: None above threshold {self._score_threshold}")
                return "", []
            
            # Build context and attributions
            context_parts = []
            attributions = []
            
            # Log the retrieval
            rag_retrieval_logger.info("=" * 60)
            rag_retrieval_logger.info(f"QUERY: {query}")
            rag_retrieval_logger.info("-" * 40)
            
            for doc, score in filtered_results:
                section_path = doc.metadata.get('section_path', 'Unknown Section')
                chunk_idx = doc.metadata.get('chunk_index', 0)
                doc_idx = doc.metadata.get('doc_index', 0)
                
                attribution = {
                    'section': section_path,
                    'doc_index': doc_idx,
                    'chunk_index': chunk_idx,
                    'score': round(score, 3),
                    'content_preview': doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                }
                attributions.append(attribution)
                
                # Add to context with source marker
                context_parts.append(f"[Source: {section_path}]\n{doc.page_content}")
                
                # Log to RAG retrieval file
                rag_retrieval_logger.info(f"MATCH {len(attributions)}: Score={score:.3f}")
                rag_retrieval_logger.info(f"  Section: {section_path}")
                rag_retrieval_logger.info(f"  Content: {doc.page_content}")
                rag_retrieval_logger.info("-" * 40)
            
            context = "\n\n".join(context_parts)
            
            # Truncate if too long
            if len(context) > Config.RAG_MAX_CONTEXT_LENGTH:
                context = context[:Config.RAG_MAX_CONTEXT_LENGTH] + "..."
            
            logger.info(f"Retrieved {len(filtered_results)} chunks for query (total {len(context)} chars)")
            
            return context, attributions
            
        except Exception as e:
            logger.error(f"Error searching context: {e}", exc_info=True)
            return "", []
    
    def get_source_attribution_text(self, attributions: List[Dict[str, Any]]) -> str:
        """
        Generate human-readable source attribution text.
        
        Args:
            attributions: List of attribution dictionaries.
        
        Returns:
            Formatted attribution string.
        """
        if not attributions:
            return ""
        
        lines = ["Information retrieved from:"]
        for i, attr in enumerate(attributions, 1):
            lines.append(f"  {i}. {attr['section']} (relevance: {attr['score']:.0%})")
        
        return "\n".join(lines)
    
    @property
    def is_ready(self) -> bool:
        """Check if the RAG handler is ready to use."""
        return self._vectorstore is not None and self._embeddings is not None
