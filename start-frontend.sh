#!/bin/bash

# Start Frontend Server
echo "Starting Sankalpam Frontend Server..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Check if .env.local file exists
if [ ! -f .env.local ]; then
    echo "Creating .env.local file..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
    echo "NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-google-maps-api-key" >> .env.local
fi

# Start the dev server
echo "Starting Next.js dev server on http://localhost:3000"
npm run dev

