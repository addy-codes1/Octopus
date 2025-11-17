"""Vector store service for document embeddings."""
from typing import Optional
from uuid import UUID

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from ..core.config import get_settings

settings = get_settings()


class VectorStoreService:
    """Service for managing document embeddings in Chroma."""

    def __init__(self):
        """Initialize the vector store service."""
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def _get_collection_name(self, user_id: UUID) -> str:
        """Get collection name for a user."""
        return f"user_{str(user_id).replace('-', '_')}"

    def _get_user_vectorstore(self, user_id: UUID) -> Chroma:
        """Get or create a Chroma collection for a user."""
        return Chroma(
            collection_name=self._get_collection_name(user_id),
            embedding_function=self.embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        )

    def add_paper(
        self,
        user_id: UUID,
        paper_id: UUID,
        title: str,
        text: str,
        metadata: Optional[dict] = None
    ) -> int:
        """
        Add a paper's text to the vector store.

        Returns the number of chunks created.
        """
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)

        # Create documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc_metadata = {
                "paper_id": str(paper_id),
                "paper_title": title,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            if metadata:
                doc_metadata.update(metadata)

            documents.append(Document(
                page_content=chunk,
                metadata=doc_metadata
            ))

        # Add to vector store
        vectorstore = self._get_user_vectorstore(user_id)
        vectorstore.add_documents(documents)

        return len(documents)

    def search(
        self,
        user_id: UUID,
        query: str,
        paper_ids: Optional[list[UUID]] = None,
        k: int = None
    ) -> list[Document]:
        """
        Search for relevant documents.

        Args:
            user_id: User's ID
            query: Search query
            paper_ids: Optional list of paper IDs to filter by
            k: Number of results to return
        """
        if k is None:
            k = settings.VECTOR_SEARCH_K

        vectorstore = self._get_user_vectorstore(user_id)

        if paper_ids:
            # Filter by specific papers
            filter_dict = {
                "paper_id": {"$in": [str(pid) for pid in paper_ids]}
            }
            results = vectorstore.similarity_search(query, k=k, filter=filter_dict)
        else:
            # Search all user's papers
            results = vectorstore.similarity_search(query, k=k)

        return results

    def delete_paper(self, user_id: UUID, paper_id: UUID) -> None:
        """Delete all chunks for a specific paper."""
        vectorstore = self._get_user_vectorstore(user_id)

        # Get all document IDs for this paper
        # Note: Chroma doesn't have a direct delete by metadata, so we need to work around
        # This is a simplified approach - in production, you'd track document IDs
        try:
            collection = vectorstore._collection
            results = collection.get(
                where={"paper_id": str(paper_id)},
                include=[]
            )
            if results and results["ids"]:
                collection.delete(ids=results["ids"])
        except Exception:
            # If collection doesn't exist or is empty, nothing to delete
            pass

    def get_paper_count(self, user_id: UUID) -> int:
        """Get the number of unique papers in the user's collection."""
        try:
            vectorstore = self._get_user_vectorstore(user_id)
            collection = vectorstore._collection
            results = collection.get(include=["metadatas"])

            if results and results["metadatas"]:
                paper_ids = set()
                for metadata in results["metadatas"]:
                    if "paper_id" in metadata:
                        paper_ids.add(metadata["paper_id"])
                return len(paper_ids)
        except Exception:
            pass

        return 0
