#!/bin/bash

echo "🐍 Creating Python virtual environment..."
python3 -m venv .venv

echo "✅ Activating virtual environment..."
source .venv/bin/activate

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🔑 Creating .env template..."
cat <<EOT > .env
# Azure OpenAI API configuration
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
EOT

echo "✅ Setup complete. Activate with: source .venv/bin/activate"
