import os
import logging
from typing import Optional, Any
from langchain_core.language_models.chat_models import BaseChatModel
from backend.app.config import settings

logger = logging.getLogger(__name__)

def get_llm(streaming: bool = False, temperature: float = 0.0) -> Optional[BaseChatModel]:
    """
    Returns an instantiated LangChain ChatModel according to configuration.
    Priority:
    1. Groq (if GROQ_API_KEY is available and provider is 'auto' or 'groq')
    2. OpenAI (if OPENAI_API_KEY is available and provider is 'auto' or 'openai')
    3. Google Gemini (if GEMINI_API_KEY is available)
    """
    provider = settings.LLM_PROVIDER.lower()
    
    # 1. Groq (Fast & Free)
    if (provider in ("auto", "groq")) and settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("your_"):
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=settings.GROQ_MODEL,
                temperature=temperature,
                streaming=streaming,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ChatGroq: {e}")

    # 2. OpenAI
    if (provider in ("auto", "openai")) and settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your_"):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                temperature=temperature,
                streaming=streaming,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ChatOpenAI: {e}")

    # 3. Gemini
    if (provider in ("auto", "gemini")) and settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                google_api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL,
                temperature=temperature,
                streaming=streaming,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ChatGoogleGenerativeAI: {e}")

    logger.info("No active external LLM API key detected or provider offline. Using intelligent fallback mode.")
    return None
