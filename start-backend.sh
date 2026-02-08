#!/bin/bash

# Start Backend Server
echo "Starting Sankalpam Backend Server..."
cd backend

# Activate virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env 2>/dev/null || echo "Note: Please create .env file manually"
fi

# Start the server
echo "Starting FastAPI server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
uvicorn main:app --reload --host 0.0.0.0 --port 8000

