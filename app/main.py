"""FastAPI application for SEO article generation."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    settings = get_settings()

    # Startup
    logger.info("Starting SEO Article Generator API")
    logger.info(f"Data directory: {settings.data_dir}")

    # Ensure directories exist
    settings.jobs_dir.mkdir(parents=True, exist_ok=True)

    # Log provider status
    if settings.use_mock_serp:
        logger.info("Using MOCK SERP provider")
    elif settings.has_serper_key:
        logger.info("Using Serper.dev SERP provider")
    else:
        logger.warning("No SERP API key configured, falling back to mock")

    if settings.use_mock_llm:
        logger.info("Using MOCK LLM provider")
    elif settings.has_groq_key:
        logger.info(f"Using Groq LLM provider (model: {settings.llm_model})")
    else:
        logger.warning("No LLM API key configured, falling back to mock")

    yield

    # Shutdown
    logger.info("Shutting down SEO Article Generator API")


# Create FastAPI app
app = FastAPI(
    title="SEO Article Generator",
    description="""
An AI-powered backend service that generates SEO-optimized articles.

## Features

- **SERP Analysis**: Analyzes top search results for your topic
- **Theme Extraction**: Identifies common themes and search intent
- **Outline Generation**: Creates structured article outlines
- **Article Generation**: Produces full, publish-ready articles
- **SEO Validation**: Validates and scores SEO compliance
- **Job Persistence**: Resume interrupted jobs from checkpoints

## Quick Start

1. Create a job: `POST /jobs` with your topic
2. Check status: `GET /jobs/{job_id}/status`
3. Get results: `GET /jobs/{job_id}` when complete
    """,
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["jobs"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SEO Article Generator API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
