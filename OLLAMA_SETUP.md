# Ollama Setup Guide for CodeGuard

## What is Ollama?

Ollama is a tool that allows you to run Large Language Models (LLMs) locally on your computer. This means:
- ✅ **Privacy**: Your code never leaves your machine
- ✅ **Free**: No API costs or usage limits
- ✅ **Fast**: Local processing with no network latency
- ✅ **Offline**: Works without internet connection

## Installation

### Windows
1. Download Ollama from [https://ollama.ai/download](https://ollama.ai/download)
2. Run the installer (OllamaSetup.exe)
3. Ollama will be installed and start automatically

### Mac
```bash
curl https://ollama.ai/install.sh | sh
```

### Linux
```bash
curl https://ollama.ai/install.sh | sh
```

## Pulling Models

After installation, open a terminal and pull a model:

### For General Code Analysis (Recommended)
```bash
ollama pull llama2
```

### For Better Code Analysis (Specialized)
```bash
ollama pull codellama
```

### Other Options
```bash
# Smaller, faster model
ollama pull mistral

# Larger, more capable model
ollama pull llama2:13b

# Python-specific model
ollama pull codellama:python
```

## Running Ollama

### Windows
Ollama runs automatically as a service after installation. You can check if it's running:
```powershell
curl http://localhost:11434
```

If not running, start it from Start Menu: "Ollama"

### Mac/Linux
```bash
ollama serve
```

## Configuring CodeGuard

Edit your `.env` file:
```bash
# Choose your model
OLLAMA_MODEL=codellama

# Default host (usually don't need to change)
OLLAMA_HOST=http://localhost:11434
```

## Testing Ollama

Test if Ollama is working:
```bash
ollama run llama2 "Hello, can you help me analyze code?"
```

## Model Comparison

| Model | Size | Speed | Code Quality | Best For |
|-------|------|-------|--------------|----------|
| llama2 | 3.8GB | Fast | Good | General use, quick analysis |
| codellama | 3.8GB | Fast | Excellent | Code-specific analysis (Recommended) |
| mistral | 4.1GB | Very Fast | Good | Quick reviews |
| llama2:13b | 7.3GB | Medium | Excellent | Detailed analysis |
| codellama:python | 3.8GB | Fast | Excellent | Python-only projects |

## Troubleshooting

### Ollama not responding
```bash
# Check if Ollama is running
curl http://localhost:11434

# Restart Ollama
# Windows: Restart from Start Menu
# Mac/Linux: 
killall ollama
ollama serve
```

### Model not found
```bash
# List installed models
ollama list

# Pull the model again
ollama pull codellama
```

### Out of memory
- Use a smaller model (mistral, llama2:7b)
- Close other applications
- Increase system swap/page file

### Slow performance
- Use a smaller model
- Ensure Ollama is using GPU (if available)
- Close unnecessary applications

## GPU Support

Ollama automatically uses GPU if available:
- **NVIDIA**: Requires CUDA
- **AMD**: Requires ROCm (Linux only)
- **Apple Silicon**: Uses Metal automatically

## Model Management

```bash
# List all installed models
ollama list

# Remove a model
ollama rm llama2

# Update a model
ollama pull llama2

# Show model info
ollama show llama2
```

## Advanced Configuration

### Custom Model Parameters
You can customize model behavior in CodeGuard by modifying the `ollama.chat()` call in `app.py`:

```python
response = ollama.chat(
    model=OLLAMA_MODEL,
    messages=[...],
    options={
        'temperature': 0.3,  # Lower = more focused
        'top_p': 0.9,
        'top_k': 40,
    }
)
```

### Using Different Hosts
If running Ollama on another machine:
```bash
# In .env
OLLAMA_HOST=http://192.168.1.100:11434
```

## Performance Tips

1. **First run is slow**: Model loads into memory
2. **Keep Ollama running**: Subsequent requests are faster
3. **Use appropriate model**: Bigger ≠ always better
4. **Monitor resources**: Check CPU/GPU/RAM usage

## Privacy & Security

- ✅ All processing happens locally
- ✅ No data sent to external servers
- ✅ Your code remains on your machine
- ✅ No API keys or accounts needed

## Resources

- Official Website: [https://ollama.ai](https://ollama.ai)
- Documentation: [https://github.com/ollama/ollama](https://github.com/ollama/ollama)
- Models Library: [https://ollama.ai/library](https://ollama.ai/library)

---

**Ready to analyze code privately with AI!** 🚀
