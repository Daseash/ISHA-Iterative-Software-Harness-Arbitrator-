#!/usr/bin/env bash
set -e

echo "🚀 Installing ISHA (Iterative Software Harness Arbitrator)..."

# 1. Check git
if ! command -v git &> /dev/null; then
    echo "❌ Git is required but not installed. Please install Git first."
    exit 1
fi

# 2. Check python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Python 3.10+ is required but not installed. Please install Python first."
    exit 1
fi

# 3. Clone or update repository into isha-agent
INSTALL_DIR="isha-agent"
if [ -d "$INSTALL_DIR" ]; then
    echo "📁 Directory $INSTALL_DIR already exists. Updating..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "📦 Cloning ISHA into ./$INSTALL_DIR..."
    git clone https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 4. Install dependencies
echo "📦 Installing Python dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt
$PYTHON_CMD -m pip install -e .

echo ""
echo "✅ ISHA installation complete!"
echo "👉 Get started by running:"
echo "   cd $INSTALL_DIR"
echo "   python -m src.cli doctor"
