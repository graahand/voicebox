"""
Vector RAG Handler module for VoiceBox project.
Implements semantic search using embeddings and FAISS for Futuruma event information.
"""

from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import sys
import re
import pickle
import numpy as np

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.config import Config


class VectorRAGHandler:
    """
    Vector-based RAG handler using sentence embeddings and FAISS.
    Implements semantic chunking, embedding generation, and similarity search.
    """
    
    _instance: Optional['VectorRAGHandler'] = None
    
    def __new__(cls) -> 'VectorRAGHandler':
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, source_file: Optional[Path] = None) -> None:
        """
        Initialize Vector RAG handler.
        
        Args:
            source_file: Path to source data file.
        """
        if self._initialized:
            return
        
        if source_file is None:
            source_file = Config.DATA_DIR / "source_data.md"
        
        self._source_file = source_file
        self._chunks: List[str] = []
        self._chunk_metadata: List[Dict[str, Any]] = []
        self._embeddings: Optional[np.ndarray] = None
        self._index = None
        self._embedding_model = None
        self._initialized = True
        
        # Configuration
        self._top_k = Config.RAG_TOP_K
        self._score_threshold = Config.RAG_SCORE_THRESHOLD
        self._chunk_size = Config.RAG_CHUNK_SIZE
        self._chunk_overlap = Config.RAG_CHUNK_OVERLAP
        self._max_context_length = Config.RAG_MAX_CONTEXT_LENGTH
        
        # Initialize the system
        self._init_embedding_model()
        self._load_and_process_document()
    
    def _init_embedding_model(self) -> None:
        """Initialize the sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            print(f"Loading embedding model: {Config.RAG_EMBEDDING_MODEL}")
            self._embedding_model = SentenceTransformer(Config.RAG_EMBEDDING_MODEL)
            print(f"Embedding model loaded (dim={Config.RAG_VECTOR_DIMENSION})")
            
        except ImportError:
            print("Error: sentence-transformers not installed")
            print("Install with: pip install sentence-transformers")
            self._embedding_model = None
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            self._embedding_model = None
    
    def _load_and_process_document(self) -> None:
        """Load document, chunk it, generate embeddings, and build FAISS index."""
        if self._embedding_model is None:
            print("Cannot process document: embedding model not loaded")
            return
        
        try:
            # Load document
            if not self._source_file.exists():
                print(f"Warning: Source file not found: {self._source_file}")
                return
            
            with open(self._source_file, 'r', encoding='utf-8') as file:
                full_text = file.read()
            
            print(f"RAG: Loaded document from {self._source_file}")
            
            # Semantic chunking
            self._chunks, self._chunk_metadata = self._semantic_chunking(full_text)
            print(f"RAG: Created {len(self._chunks)} semantic chunks")
            
            # Generate embeddings
            self._embeddings = self._generate_embeddings(self._chunks)
            print(f"RAG: Generated embeddings ({self._embeddings.shape})")
            
            # Build FAISS index
            self._build_faiss_index()
            print(f"RAG: Built FAISS index (type={Config.RAG_FAISS_INDEX_TYPE})")
            
        except Exception as e:
            print(f"Error processing document: {e}")
            import traceback
            traceback.print_exc()
    
    def _semantic_chunking(self, text: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Chunk document semantically based on structure and sentences.
        
        Args:
            text: Full document text.
        
        Returns:
            Tuple of chunks and their metadata.
        """
        chunks = []
        metadata = []
        
        # Split by major sections (headers)
        sections = re.split(r'\n(?=#+\s)', text)
        
        for section_idx, section in enumerate(sections):
            if not section.strip():
                continue
            
            # Extract section title
            header_match = re.match(r'(#+)\s+(.+)', section)
            section_title = header_match.group(2) if header_match else "Introduction"
            
            # Split section into sentences
            sentences = re.split(r'(?<=[.!?])\s+', section)
            
            current_chunk = ""
            current_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Check if adding sentence exceeds chunk size
                if len(current_chunk) + len(sentence) > self._chunk_size and current_chunk:
                    # Save current chunk
                    chunks.append(current_chunk.strip())
                    metadata.append({
                        'section': section_title,
                        'chunk_index': len(chunks),
                        'sentences': current_sentences.copy()
                    })
                    
                    # Start new chunk with overlap
                    if self._chunk_overlap > 0 and current_sentences:
                        # Keep last sentence for overlap
                        overlap_text = current_sentences[-1]
                        current_chunk = overlap_text + " " + sentence
                        current_sentences = [current_sentences[-1], sentence]
                    else:
                        current_chunk = sentence
                        current_sentences = [sentence]
                else:
                    # Add to current chunk
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence
                    current_sentences.append(sentence)
            
            # Add remaining chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                metadata.append({
                    'section': section_title,
                    'chunk_index': len(chunks),
                    'sentences': current_sentences.copy()
                })
        
        return chunks, metadata
    
    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for text chunks.
        
        Args:
            texts: List of text chunks.
        
        Returns:
            Numpy array of embeddings.
        """
        if self._embedding_model is None:
            return np.array([])
        
        try:
            embeddings = self._embedding_model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True  # L2 normalize for cosine similarity
            )
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return np.array([])
    
    def _build_faiss_index(self) -> None:
        """Build FAISS index for similarity search."""
        if self._embeddings is None or len(self._embeddings) == 0:
            print("Cannot build index: no embeddings available")
            return
        
        try:
            import faiss
            
            dimension = self._embeddings.shape[1]
            
            if Config.RAG_FAISS_INDEX_TYPE.lower() == "flat":
                # Flat index for exact search (cosine similarity via inner product on normalized vectors)
                self._index = faiss.IndexFlatIP(dimension)
            else:
                # Default to Flat
                self._index = faiss.IndexFlatIP(dimension)
            
            # Add vectors to index
            self._index.add(self._embeddings.astype('float32'))
            
        except ImportError:
            print("Error: faiss not installed")
            print("Install with: pip install faiss-cpu")
            self._index = None
        except Exception as e:
            print(f"Error building FAISS index: {e}")
            self._index = None
    
    def search_context(self, query: str, max_chunks: Optional[int] = None) -> str:
        """
        Search for relevant context using vector similarity.
        
        Args:
            query: User's query.
            max_chunks: Maximum number of chunks to return (uses config if None).
        
        Returns:
            Relevant context from document.
        """
        if self._index is None or self._embedding_model is None:
            return ""
        
        if max_chunks is None:
            max_chunks = self._top_k
        
        # Check if query is Futuruma-related
        if not self.is_futuruma_related(query):
            return ""
        
        try:
            # Generate query embedding
            query_embedding = self._embedding_model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Search in FAISS index
            scores, indices = self._index.search(
                query_embedding.astype('float32'),
                max_chunks
            )
            
            # Filter by score threshold and collect chunks
            relevant_chunks = []
            current_length = 0
            
            for score, idx in zip(scores[0], indices[0]):
                # Check score threshold (cosine similarity: 0 to 1)
                if score < self._score_threshold:
                    continue
                
                chunk_text = self._chunks[idx]
                chunk_meta = self._chunk_metadata[idx]
                
                # Check context length limit
                if current_length + len(chunk_text) <= self._max_context_length:
                    relevant_chunks.append({
                        'text': chunk_text,
                        'score': float(score),
                        'section': chunk_meta['section']
                    })
                    current_length += len(chunk_text)
                else:
                    break
            
            if not relevant_chunks:
                return ""
            
            # Format context
            context_parts = []
            for chunk in relevant_chunks:
                context_parts.append(f"[{chunk['section']}] {chunk['text']}")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            print(f"Error during search: {e}")
            return ""
    
    def is_futuruma_related(self, query: str) -> bool:
        """Check if query is Futuruma-related."""
        query_lower = query.lower()
        
        keywords = [
            'futuruma', 'future-rama', 'event', 'tech fest', 'nepal', 'project',
            'robotics', 'ai', 'cybersecurity', 'venue', 'ing skill academy',
            'skill museum', 'smarc', 'dermascan', 'laser tag', 'showcase'
        ]
        
        return any(keyword in query_lower for keyword in keywords)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        return {
            'num_chunks': len(self._chunks),
            'embedding_dimension': Config.RAG_VECTOR_DIMENSION,
            'model': Config.RAG_EMBEDDING_MODEL,
            'index_type': Config.RAG_FAISS_INDEX_TYPE,
            'score_threshold': self._score_threshold,
            'top_k': self._top_k,
            'search_method': 'FAISS + Cosine Similarity'
        }
    
    @property
    def source_file(self) -> Path:
        """Get source file path."""
        return self._source_file


def main() -> None:
    """Test vector RAG handler."""
    print("="*60)
    print("Vector RAG Handler Test")
    print("="*60)
    
    rag = VectorRAGHandler()
    
    print(f"\nStatistics:")
    stats = rag.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test queries
    test_queries = [
        "What is Futuruma?",
        "Tell me about AI projects",
        "Which cities host the event?",
        "What is DermaScan?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        context = rag.search_context(query)
        if context:
            print(f"Context length: {len(context)} chars")
            print(f"\n{context[:300]}...")
        else:
            print("No relevant context found")


if __name__ == '__main__':
    main()
