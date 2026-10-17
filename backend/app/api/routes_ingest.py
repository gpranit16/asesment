from fastapi import APIRouter, Query
from backend.app.rag.ingest import ingest_pdf

router = APIRouter(tags=["ingest"])

@router.post("/ingest")
async def trigger_ingestion(force: bool = Query(False, description="Force re-indexing of the PDF")):
    """Trigger ingestion of the public reference PDF into ChromaDB."""
    result = ingest_pdf(force_reindex=force)
    return {
        "success": True,
        "details": result
    }
