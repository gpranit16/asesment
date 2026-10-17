import logging
from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.rag.ingest import get_chroma_client, get_embedding_function, COLLECTION_NAME, ingest_pdf

logger = logging.getLogger(__name__)

class HandbookRetriever:
    def __init__(self):
        self.client = get_chroma_client()
        self.embedding_fn = get_embedding_function()
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            self.collection = self.client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=self.embedding_fn
            )
        except Exception:
            logger.info("Collection not found in retriever initialization. Triggering ingestion...")
            ingest_pdf(force_reindex=False)
            self.collection = self.client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=self.embedding_fn
            )

    def query(self, query_text: str, top_k: int = settings.TOP_K_RESULTS) -> Dict[str, Any]:
        """
        Queries ChromaDB for semantically matching passages.
        Returns combined text with explicit page citations and structured metadata.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        documents = results["documents"][0] if results.get("documents") else []
        metadatas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []

        sources: List[Dict[str, Any]] = []
        context_parts: List[str] = []
        cited_pages: List[int] = []

        for doc, meta, dist in zip(documents, metadatas, distances):
            page = meta.get("page", 1)
            chunk_id = meta.get("chunk_id", "")
            cited_pages.append(page)
            
            sources.append({
                "page": page,
                "source": meta.get("source", "employee_handbook.pdf"),
                "chunk_id": chunk_id,
                "distance": float(dist),
                "snippet": doc[:200] + "..." if len(doc) > 200 else doc,
                "full_text": doc
            })

            context_parts.append(f"[Handbook Page {page}]:\n{doc}")

        primary_page = cited_pages[0] if cited_pages else 1

        return {
            "query": query_text,
            "context_text": "\n\n---\n\n".join(context_parts),
            "sources": sources,
            "primary_page": primary_page,
            "cited_pages": sorted(list(set(cited_pages)))
        }

retriever = HandbookRetriever()
