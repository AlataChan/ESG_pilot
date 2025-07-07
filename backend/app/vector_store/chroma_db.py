import chromadb
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict, Any
import logging
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

from app.core.config import settings
from app.core.llm_factory import llm_factory

logger = logging.getLogger(__name__)

# ChromaDB's new interface requires a specific signature for embedding functions.
# We create an adapter class to bridge LangChain's embedding models with ChromaDB's expectations.
class LangchainEmbeddingFunctionAdapter(EmbeddingFunction):
    def __init__(self, langchain_embedding: OpenAIEmbeddings):
        self._langchain_embedding = langchain_embedding

    def __call__(self, input: Documents) -> Embeddings:
        """
        The method that ChromaDB will invoke to get embeddings.
        It calls the underlying LangChain embedding model.
        """
        return self._langchain_embedding.embed_documents(input)

class ChromaDBManager:
    """
    Manages interactions with the ChromaDB vector store.
    """
    _instance = None

    def __init__(self):
        if ChromaDBManager._instance:
            raise RuntimeError("ChromaDBManager is a singleton, use get_chroma_manager() to get the instance.")
        
        logging.info("Initializing ChromaDBManager...")
        
        # 1. Initialize the LangChain Embedding model - 使用LLM工厂
        lc_embedding_model = llm_factory.create_embedding_model()

        # 2. Wrap it with our adapter
        self.embedding_function = LangchainEmbeddingFunctionAdapter(lc_embedding_model)

        # 3. Initialize the ChromaDB client
        if settings.ENV_STATE in ["local", "test"]:
            logging.info(f"Using local, persistent ChromaDB at: {settings.CHROMA_DB_PATH}")
            # Use a persistent client for local development/testing
            self.client = chromadb.PersistentClient(path=str(settings.CHROMA_DB_PATH))
        else:
            logging.info(f"Connecting to remote ChromaDB at: {settings.CHROMA_DB_HOST}:{settings.CHROMA_DB_PORT}")
            # Use a HTTP client for Docker/production environment
            self.client = chromadb.HttpClient(
                host=settings.CHROMA_DB_HOST,
                port=settings.CHROMA_DB_PORT
            )

        # 4. Get or create the collection, now passing the compliant adapter
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"} 
        )
        
        logging.info(f"ChromaDBManager initialized. Collection '{settings.CHROMA_COLLECTION_NAME}' loaded/created.")
        ChromaDBManager._instance = self

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """
        Add documents to the collection.
        The embedding function adapter will handle the embedding process.
        """
        # Use the adapter to get embeddings - call it directly since it implements __call__
        embeddings = self.embedding_function(documents)
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Query the collection for similar documents.
        """
        # For query, we need to use the LangChain embedding's embed_query method directly
        query_embedding = self.embedding_function._langchain_embedding.embed_query(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results

_chroma_manager_instance = None

def get_chroma_manager():
    """
    Returns a singleton instance of the ChromaDBManager.
    Lazily initializes the manager on first call.
    """
    global _chroma_manager_instance
    if _chroma_manager_instance is None:
        logger.info("Initializing ChromaDBManager singleton...")
        _chroma_manager_instance = ChromaDBManager()
    return _chroma_manager_instance

# Deprecated: The manager is now loaded lazily via get_chroma_manager()
# chroma_manager = ChromaDBManager() 