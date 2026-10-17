import os
import urllib.request
import logging
from pathlib import Path
from typing import List, Dict, Any

import pypdf
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.app.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "handbook_knowledge"

def ensure_pdf_downloaded() -> Path:
    """Ensures the reference employee handbook PDF is downloaded."""
    pdf_path = settings.PDF_PATH
    if not pdf_path.exists():
        logger.info(f"Downloading reference PDF from {settings.PDF_URL}...")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(settings.PDF_URL, str(pdf_path))
        logger.info(f"PDF saved to {pdf_path}")
    return pdf_path

def get_chroma_client() -> chromadb.PersistentClient:
    """Returns a persistent ChromaDB client."""
    settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIR))

def get_embedding_function():
    """Returns the local MiniLM-L6-v2 embedding function."""
    return embedding_functions.DefaultEmbeddingFunction()

def ingest_pdf(force_reindex: bool = False) -> Dict[str, Any]:
    """
    Parses the employee handbook PDF, splits into chunks, and indexes into ChromaDB.
    Preserves exact page numbers for citation accuracy.
    """
    pdf_path = ensure_pdf_downloaded()
    client = get_chroma_client()
    embedding_fn = get_embedding_function()

    # Check if collection already exists with data
    existing_collections = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing_collections:
        collection = client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)
        count = collection.count()
        if count > 0 and not force_reindex:
            logger.info(f"Collection '{COLLECTION_NAME}' already contains {count} chunks. Skipping re-indexing.")
            return {"status": "already_indexed", "chunks_count": count}
        if force_reindex:
            client.delete_collection(name=COLLECTION_NAME)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    logger.info(f"Reading PDF from {pdf_path}...")
    reader = pypdf.PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    chunk_idx = 0
    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1  # 1-indexed
        page_text = page.extract_text() or ""
        page_text = page_text.strip()
        if not page_text:
            continue

        page_chunks = text_splitter.split_text(page_text)
        for chunk_in_page_idx, chunk in enumerate(page_chunks):
            chunk_idx += 1
            doc_id = f"doc_p{page_num}_c{chunk_in_page_idx + 1}"
            documents.append(chunk)
            metadatas.append({
                "page": page_num,
                "source": "employee_handbook.pdf",
                "chunk_id": doc_id,
            })
            ids.append(doc_id)

    if documents:
        # Chroma handles batch ingestion
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Successfully indexed {len(documents)} chunks from {total_pages} pages into ChromaDB.")

    return {
        "status": "success",
        "total_pages": total_pages,
        "chunks_count": len(documents),
        "collection": COLLECTION_NAME
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = ingest_pdf(force_reindex=True)
    print("Ingestion Result:", res)
