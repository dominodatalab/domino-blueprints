#!/usr/bin/env bash

# Domino App Deployment Script for FSI Onboarding App
# This script starts the Streamlit application with Domino-compatible settings

# Install requirements using pip with --upgrade to ensure correct versions
pip install --upgrade -r requirements.txt --user

# Set the port (Domino uses port 8888 for apps)
export STREAMLIT_SERVER_PORT=8888

# Disable CORS for internal Domino usage
export STREAMLIT_SERVER_ENABLE_CORS=false

# Enable WebSocket compression for better performance
export STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=true

# Run the Streamlit app using python -m to ensure correct environment
python -m streamlit run app.py \
  --server.port=8888 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableWebsocketCompression=true \
  --browser.gatherUsageStats=false
