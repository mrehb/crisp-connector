#!/bin/bash
# Local setup script for Crisp Connector

echo "🚀 Setting up Crisp Connector locally..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your API credentials:"
    echo "   - CRISP_WEBSITE_ID"
    echo "   - CRISP_API_IDENTIFIER"
    echo "   - CRISP_API_KEY"
    echo "   - IP2LOCATION_API_KEY"
    echo ""
    echo "Press Enter when you've updated .env with your credentials..."
    read
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "To test the webhook, run (in another terminal):"
echo "  source venv/bin/activate"
echo "  python test_local.py"
echo ""

