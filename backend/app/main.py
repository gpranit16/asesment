import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.rag.ingest import ingest_pdf
from backend.app.api.routes_chat import router as chat_router
from backend.app.api.routes_slots import router as slots_router
from backend.app.api.routes_ingest import router as ingest_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("enterprise_agent")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup initialization: Ensures handbook PDF is downloaded and indexed in ChromaDB."""
    logger.info("Initializing Enterprise Multi-Agent Backend...")
    try:
        ingestion_result = ingest_pdf(force_reindex=False)
        logger.info(f"Knowledge Base Status: {ingestion_result}")
    except Exception as e:
        logger.error(f"Automatic PDF ingestion during startup failed: {e}")
    yield
    logger.info("Shutting down Enterprise Multi-Agent Backend.")

app = FastAPI(
    title="Enterprise Multi-Agent Assistant API",
    description="Stateful LangGraph Agentic API with PDF RAG (ChromaDB) and Transactional Tool Calling",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers under /api
app.include_router(chat_router, prefix=settings.API_V1_PREFIX)
app.include_router(slots_router, prefix=settings.API_V1_PREFIX)
app.include_router(ingest_router, prefix=settings.API_V1_PREFIX)

@app.get("/api/health")
async def health_check():
    """Health check endpoint for Docker and monitoring."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "chroma_dir": str(settings.CHROMA_PERSIST_DIR),
        "checkpointer": str(settings.SQLITE_CHECKPOINT_PATH),
        "llm_provider": settings.LLM_PROVIDER
    }

@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "health_url": "/api/health"
    }
