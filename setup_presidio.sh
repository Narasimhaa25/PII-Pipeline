#!/bin/bash

# Setup script for Presidio PII Agent

echo "=========================================="
echo "Setting up Presidio PII Agent"
echo "=========================================="
echo ""

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating one first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install presidio-analyzer presidio-anonymizer spacy

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python packages"
    exit 1
fi

echo "✓ Python packages installed"
echo ""

# Download spaCy language model
echo "📥 Downloading spaCy language model (en_core_web_lg)..."
echo "   This may take a few minutes (~500MB)..."
python -m spacy download en_core_web_lg

if [ $? -ne 0 ]; then
    echo "❌ Failed to download spaCy model"
    echo "   Try manually: python -m spacy download en_core_web_lg"
    exit 1
fi

echo "✓ spaCy model downloaded"
echo ""

# Test the installation
echo "🧪 Testing Presidio installation..."
python -c "from presidio_analyzer import AnalyzerEngine; from presidio_anonymizer import AnonymizerEngine; print('✓ Presidio imports successful')"

if [ $? -ne 0 ]; then
    echo "❌ Presidio test failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Presidio setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Test the agent: python consumer/pii_agent_presidio.py"
echo "  2. Run the consumer: python consumer/pii_masker_presidio.py"
echo ""
echo "See AGENTS_COMPARISON.md for more details."
