# app.py
"""Main FastAPI application."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import query, retrieval, health

# Root path for reverse proxy (e.g., "/apps/airline-disaster")
# This makes Swagger docs work correctly behind a proxy
ROOT_PATH = os.environ.get("ROOT_PATH", "")

app = FastAPI(
    title="Agentic RAG Aviation Safety",
    description="Demonstrates agentic retrieval vs traditional RAG using aviation safety data",
    version="0.1.0",
    root_path=ROOT_PATH,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(retrieval.router, prefix="/retrieve", tags=["Retrieval"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Agentic RAG Aviation Safety Demo",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "query": "/api/query",
            "baseline": "/api/query/baseline",
            "retrieve_incidents": "/retrieve/incidents",
            "retrieve_regulations": "/retrieve/regulations",
            "retrieve_news": "/retrieve/news",
            "health": "/health",
        },
    }


