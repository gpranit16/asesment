import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "Enterprise Multi-Agent Assistant"
    API_V1_PREFIX: str = "/api"
    
    # LLM Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Preferred model provider: "groq", "openai", "gemini", or "auto"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # Paths
    PDF_PATH: Path = DATA_DIR / "employee_handbook.pdf"
    PDF_URL: str = "https://raw.githubusercontent.com/Azure-Samples/azure-search-openai-demo/main/data/employee_handbook.pdf"
    CHROMA_PERSIST_DIR: Path = DATA_DIR / "chroma_db"
    SQLITE_CHECKPOINT_PATH: Path = DATA_DIR / "checkpoints.sqlite"
    BOOKINGS_PATH: Path = DATA_DIR / "bookings.json"
    
    # RAG Settings
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K_RESULTS: int = 3

settings = Settings()
