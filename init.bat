@echo off

echo 🐍 Creating Python virtual environment...
python -m venv .venv

echo ✅ Activating virtual environment...
call .venv\Scripts\activate

echo 📦 Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo 🔑 Creating .env file...
echo AZURE_OPENAI_API_KEY=your-api-key-here> .env
echo AZURE_OPENAI_API_VERSION=2024-02-15-preview>> .env
echo AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/>> .env
echo AZURE_OPENAI_DEPLOYMENT=gpt-4o>> .env

echo ✅ Setup complete. Activate with: .venv\Scripts\activate
