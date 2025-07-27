#!/bin/bash
# PDF Extractor Installation Script

set -e  # Exit on error

echo "🚀 PDF Extractor Quick Install"
echo "=============================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    echo "✅ uv installed successfully"
else
    echo "✅ uv is already installed"
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
uv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source .venv/Scripts/activate
else
    # macOS/Linux
    source .venv/bin/activate
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv pip install -e .

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Configure Claude Desktop (see README for details)"
echo ""
echo "3. Start using the PDF RAG system in Claude!"