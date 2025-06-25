#!/bin/bash

# MAPSHOCK MVP Start Script
echo "🚀 Starting MAPSHOCK Intelligence Platform MVP..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.11 or later."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is required. Please install pip."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your API keys before running again."
    echo "📝 Required: OPENAI_API_KEY and/or ANTHROPIC_API_KEY"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "📦 Installing uvicorn..."
    pip install uvicorn[standard]
fi

# Start the server
echo "🎯 Starting MAPSHOCK server on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "❤️  Health Check: http://localhost:8000/health"
echo "🛡️  Protocols: http://localhost:8000/api/v1/protocols"
echo ""
echo "💡 To test your MVP, run: python test_client.py"
echo "🔌 For Lobe Chat integration, see: lobe-chat-plugin/mapshock-plugin.ts"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI server
uvicorn mapshock-backend.main:app --host 0.0.0.0 --port 8000 --reload 