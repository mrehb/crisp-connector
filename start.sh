#!/bin/bash
# Quick start script for Crisp Integration

echo "🚀 Starting Crisp Integration Server..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create .env file from env.example:"
    echo "  cp env.example .env"
    echo "  # Then edit .env with your API credentials"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Run the application
echo "✅ Starting server..."
echo "📡 Server will be available at http://localhost:5000"
echo "🔍 Health check: http://localhost:5000/health"
echo "📝 Webhook endpoint: http://localhost:5000/webhook/jotform"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py

