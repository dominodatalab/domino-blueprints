#!/bin/bash

#curl -L https://github.com/qdrant/qdrant-web-ui/releases/download/v0.2.8/dist-qdrant.zip -o drant-web-ui.zip
#
# Qdrant startup script for Domino Apps
#
# Environment variables:
#   QDRANT_PORT - HTTP port (default: 8888)
#   QDRANT_STORAGE_PATH - Storage path (default: /domino/datasets/local/rag-is-not-enough/qdrant_data)
#   QDRANT_BINARY_PATH - Path to qdrant binary (default: /domino/datasets/local/rag-is-not-enough/qdrant)

set -e

# Configuration
QDRANT_PORT=${QDRANT_PORT:-8888}
QDRANT_STORAGE_PATH=${QDRANT_STORAGE_PATH:-/domino/datasets/local/rag-is-not-enough/qdrant_data}
QDRANT_BINARY_PATH=${QDRANT_BINARY_PATH:-/domino/datasets/local/rag-is-not-enough/qdrant}

echo "Starting Qdrant..."
echo "  Port: ${QDRANT_PORT}"
echo "  Storage: ${QDRANT_STORAGE_PATH}"
echo "  Binary: ${QDRANT_BINARY_PATH}"

# Create storage directory if it doesn't exist
mkdir -p "${QDRANT_STORAGE_PATH}"

# Start Qdrant
QDRANT__SERVICE__HTTP_PORT=${QDRANT_PORT} \
QDRANT__STORAGE__STORAGE_PATH=${QDRANT_STORAGE_PATH} \
${QDRANT_BINARY_PATH}
