#!/bin/bash
# Agentic RAG API startup script for Domino Apps
#
# This script installs the package from pyproject.toml and starts the FastAPI server.
#
# Required environment variables:
#   ANTHROPIC_API_KEY or OPENAI_API_KEY - LLM API key
#   QDRANT_URL - Qdrant server URL
#
# Optional environment variables:
#   LLM_PROVIDER - "anthropic" (default) or "openai"
#   REFINEMENT_MODEL - Model for refinement tasks
#   GENERATION_MODEL - Model for answer generation
#   MLFLOW_TRACKING_URI - MLflow server URL
#   MLFLOW_EXPERIMENT_NAME - Experiment name for tracing
#   MLFLOW_ENABLED - Enable/disable MLflow (default: true)
#   API_PORT - API server port (default: 8888)
#   API_HOST - API server host (default: 0.0.0.0)
#   PROJECT_PATH - Path to project with pyproject.toml (default: /mnt)
#   INSTALL_EXTRAS - pip extras: "domino" (default, no MLflow) or "agentic-rag" (with MLflow)
#   ROOT_PATH - Base path for reverse proxy (e.g., "/apps/airline-disaster") for Swagger docs

set -e

export PROJECT_PATH=${PROJECT_PATH:-/mnt}
export API_HOST=${API_HOST:-0.0.0.0}
export API_PORT=${API_PORT:-8888}
export ROOT_PATH=${ROOT_PATH:-}
export QDRANT_URL=${QDRANT_URL:-http://localhost:6333}

# Hugging Face model cache directory (persists models across restarts)
HF_HOME=${HF_HOME:-/domino/datasets/local/rag-is-not-enough/hf_cache}
export HF_HOME
mkdir -p "${HF_HOME}"

echo "=============================================="
echo "Agentic RAG API Startup"
echo "=============================================="
echo ""

# Check for required environment variables
echo "Checking configuration..."

if [ -z "$QDRANT_URL" ]; then
    echo "WARNING: QDRANT_URL not set, using default: http://localhost:6333"
    export QDRANT_URL="http://localhost:6333"
fi
echo "  QDRANT_URL: ${QDRANT_URL}"

# LLM Provider configuration
export LLM_PROVIDER=${LLM_PROVIDER:-anthropic}
echo "  LLM_PROVIDER: ${LLM_PROVIDER}"

if [ "$LLM_PROVIDER" = "anthropic" ]; then
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "ERROR: ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
        exit 1
    fi
    echo "  ANTHROPIC_API_KEY: [SET]"
    export REFINEMENT_MODEL=${REFINEMENT_MODEL:-claude-3-haiku-20240307}
    export GENERATION_MODEL=${GENERATION_MODEL:-claude-sonnet-4-20250514}
else
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "ERROR: OPENAI_API_KEY is required when LLM_PROVIDER=openai"
        exit 1
    fi
    echo "  OPENAI_API_KEY: [SET]"
    export REFINEMENT_MODEL=${REFINEMENT_MODEL:-gpt-4o-mini}
    export GENERATION_MODEL=${GENERATION_MODEL:-gpt-4o}
fi

echo "  REFINEMENT_MODEL: ${REFINEMENT_MODEL}"
echo "  GENERATION_MODEL: ${GENERATION_MODEL}"

# MLflow configuration
export MLFLOW_ENABLED=${MLFLOW_ENABLED:-true}
export MLFLOW_EXPERIMENT_NAME=${MLFLOW_EXPERIMENT_NAME:-agentic-rag-aviation}
echo "  MLFLOW_ENABLED: ${MLFLOW_ENABLED}"
echo "  MLFLOW_EXPERIMENT_NAME: ${MLFLOW_EXPERIMENT_NAME}"

if [ -n "$MLFLOW_TRACKING_URI" ]; then
    echo "  MLFLOW_TRACKING_URI: ${MLFLOW_TRACKING_URI}"
fi

if [ -n "$ROOT_PATH" ]; then
    echo "  ROOT_PATH: ${ROOT_PATH}"
    echo "  Swagger docs: ${ROOT_PATH}/docs"
fi

echo "  HF_HOME: ${HF_HOME}"

if [ -n "$DOMINO_API_PROXY" ]; then
    echo "  DOMINO_API_PROXY: ${DOMINO_API_PROXY}"
    echo "  Qdrant auth: Bearer token (via Domino proxy)"
else
    echo "  Qdrant auth: API key or none"
fi

echo ""

# Install package from pyproject.toml
echo "Installing package from ${PROJECT_PATH}..."
cd "${PROJECT_PATH}"

if [ -f "pyproject.toml" ]; then
    # Install with domino extras (excludes MLflow, uses Domino's tracking)
    # Use [agentic-rag] for full install including MLflow
    INSTALL_EXTRAS=${INSTALL_EXTRAS:-domino}
    echo "Installing with extras: [${INSTALL_EXTRAS}]"
    pip install -e ".[${INSTALL_EXTRAS}]" --quiet
    echo "Package installed successfully."
else
    echo "ERROR: pyproject.toml not found in ${PROJECT_PATH}"
    exit 1
fi

echo ""

# Start the API server
echo "Starting API server on ${API_HOST}:${API_PORT}..."
echo "=============================================="
echo ""

cd "${PROJECT_PATH}"
python -m uvicorn agentic_rag.endpoints.app:app \
    --host "${API_HOST}" \
    --port "${API_PORT}" \
    --workers 1
