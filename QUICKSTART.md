# CodeGuard - Quick Start Guide

## Installation (5 minutes)

### Step 1: Install Python
Download Python 3.8+ from [python.org](https://www.python.org/downloads/)

### Step 2: Setup Project
```bash
# Navigate to project directory
cd CodeGuard-app

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure
```bash
# Copy environment template
copy .env.example .env  # Windows
cp .env.example .env    # Mac/Linux

# Edit .env and change SECRET_KEY
```

### Step 4: Run
```bash
python app.py
```

Visit: http://localhost:5000

## First Steps

1. **Register** - Create your account
2. **Create Project** - Click "New Project"
3. **Upload Code** - Upload a Python/Java/JS file
4. **View Results** - See instant analysis!

## Optional: Enable AI Analysis with Ollama

1. Download Ollama from [ollama.ai](https://ollama.ai)
2. Install and pull a model:
   ```bash
   ollama pull llama2
   # For better code analysis, use:
   ollama pull codellama
   ```
3. Start Ollama server (in a separate terminal):
   ```bash
   ollama serve
   ```
4. Update `.env` if needed:
   ```
   OLLAMA_MODEL=codellama
   OLLAMA_HOST=http://localhost:11434
   ```
5. Restart the CodeGuard app

## Need Help?

Check the full [README.md](README.md) for detailed documentation.
