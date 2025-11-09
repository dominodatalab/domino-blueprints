#!/bin/bash
set -e  # Exit on error

# Check if DOMINO_BASE_URL is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <DOMINO_BASE_URL>"
    echo "Example: $0 https://cloud-cx.domino.tech"
    exit 1
fi

DOMINO_BASE_URL=$1

# Install Node
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash
. "$HOME/.nvm/nvm.sh"
nvm install 22

# Remove any pre-existing folder
rm -rf my-vite-app

# Create fresh vite project
yes | npm create vite@latest my-vite-app -- --template react --force

cd my-vite-app/

# Create vite config for Domino environment
cat << 'EOF' > vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    allowedHosts: true
  },
  base: './'
})
EOF

# Install dependencies (ignoring any problematic postinstall scripts)
echo "Installing dependencies..."
npm install --ignore-scripts --legacy-peer-deps

# Copy your actual application code from app-code folder
echo "Copying application code from app-code..."

# Copy src folder (your React components)
if [ -d "../app-code/src" ]; then
    echo "Copying src folder..."
    rm -rf src
    cp -r ../app-code/src .
fi

# Copy public folder if it exists
if [ -d "../app-code/public" ]; then
    echo "Copying public folder..."
    rm -rf public
    cp -r ../app-code/public .
fi

# Copy any additional dependencies from app-code package.json
if [ -f "../app-code/package.json" ]; then
    echo "Merging package.json dependencies..."
    node << 'NODESCRIPT'
const fs = require('fs');
const currentPkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const appCodePkg = JSON.parse(fs.readFileSync('../app-code/package.json', 'utf8'));

// Merge dependencies
if (appCodePkg.dependencies) {
    currentPkg.dependencies = { ...currentPkg.dependencies, ...appCodePkg.dependencies };
}

// Merge devDependencies
if (appCodePkg.devDependencies) {
    currentPkg.devDependencies = { ...currentPkg.devDependencies, ...appCodePkg.devDependencies };
}

fs.writeFileSync('package.json', JSON.stringify(currentPkg, null, 2));
NODESCRIPT

    # Install the merged dependencies
    echo "Installing additional dependencies from app-code..."
    npm install --ignore-scripts --legacy-peer-deps
fi

# Copy any other config files (like .env, tailwind.config.js, etc.)
for file in ../app-code/{.env,tailwind.config.js,postcss.config.js}; do
    if [ -f "$file" ]; then
        echo "Copying $(basename $file)..."
        cp "$file" .
    fi
done

# Build the app
echo "Building app..."
VITE_MODEL_API_URL=$MODEL_API_URL VITE_MODEL_API_TOKEN=$MODEL_API_TOKEN npm run build

# Remove trailing slash from DOMINO_BASE_URL if present
DOMINO_BASE_URL=${DOMINO_BASE_URL%/}

# Extract the path from JUPYTER_SERVER_URL, remove trailing slash, then add proxy path
PROXY_PATH=$(echo "$JUPYTER_SERVER_URL" | sed 's|^https\?://[^/]*||' | sed 's|/$||')
PROXY_URL="${DOMINO_BASE_URL}${PROXY_PATH}/proxy/4173/"

echo ""
echo "========================================="
echo "Preview will be available at:"
echo $PROXY_URL
echo "========================================="
echo ""

# Run preview
npm run preview -- --host 0.0.0.0 --port 4173
