# Ollama Setup Guide

## Overview

Ollama is a local LLM server that allows you to run large language models on your
own hardware without requiring API keys or internet connectivity. This guide covers
setting up Ollama for use with the RAG system.

## Quick Setup

### 1. Install Ollama

#### macOS

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Linux

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows

1. Download from [Ollama Downloads](https://ollama.ai/download)
2. Run the installer
3. Follow the installation wizard

### 2. Start Ollama Server

```bash
ollama serve
```

This starts the Ollama server on `http://localhost:11434`.

### 3. Download a Model

Choose a model based on your hardware and needs:

```bash
# Latest O3 models (recommended)
ollama pull o3:8b          # Best balance of performance and resources
ollama pull o3:70b         # Highest quality, requires more RAM
ollama pull o3:3b          # Fastest, good for simple tasks

# Legacy Llama 3.1 models
ollama pull llama3.1:8b    # Good balance, most users
ollama pull llama3.1:70b   # Best quality, high-end hardware
ollama pull llama3.1:3b    # Fast responses, basic tasks

# Specialized models
ollama pull codellama:7b   # Programming and technical tasks
ollama pull mistral:7b     # General purpose, good performance
```

### 4. Test Ollama

```bash
# Test the O3 model
ollama run o3:8b "Hello, how are you?"
```

### 5. Test RAG System

Run the test to verify everything works:

```bash
python test_rag_basic.py
```

## Configuration

Update `config/rag_config.yaml` to use Ollama:

```yaml
llm:
  type: "ollama"
  model: "o3:8b"  # or your chosen model (o3:8b, o3:70b, o3:3b)
  temperature: 0.1
  base_url: "http://localhost:11434"  # default Ollama URL
```

## Available Models

### Recommended Models

#### O3 Models (Latest - Recommended)

| Model | Size | RAM Required | Use Case |
|-------|------|--------------|----------|
| `o3:3b` | 3B | 4GB | Fast responses, basic tasks |
| `o3:8b` | 8B | 8GB | **Best balance, most users** |
| `o3:70b` | 70B | 40GB | **Highest quality, complex reasoning** |

#### Legacy Models

| Model | Size | RAM Required | Use Case |
|-------|------|--------------|----------|
| `llama3.1:3b` | 3B | 4GB | Fast responses, basic tasks |
| `llama3.1:8b` | 8B | 8GB | Good balance, most users |
| `llama3.1:70b` | 70B | 40GB | Best quality, high-end hardware |
| `codellama:7b` | 7B | 8GB | Programming and technical tasks |
| `mistral:7b` | 7B | 8GB | General purpose, good performance |

### Model Management

```bash
# List installed models
ollama list

# Remove a model
ollama rm llama3.1:3b

# Update a model
ollama pull o3:8b
```

## Hardware Requirements

### Minimum Requirements

- **RAM**: 8GB (for 8B models)
- **Storage**: 10GB free space
- **CPU**: Modern multi-core processor

### Recommended Requirements

- **RAM**: 16GB+ (for larger models)
- **Storage**: 50GB+ free space
- **GPU**: NVIDIA GPU with 8GB+ VRAM (optional but recommended)

### O3 Model Benefits

O3 models are the latest generation from Ollama, offering significant improvements:

1. **Better Performance**: Improved reasoning and response quality
2. **Enhanced Context Understanding**: Better comprehension of technical content
3. **Optimized for Local Use**: Designed specifically for local deployment
4. **Improved Safety**: Better alignment and safety features
5. **Technical Expertise**: Enhanced capabilities for technical documentation

### Performance Tips

1. **Use GPU acceleration** (if available):

   ```bash
   # Install CUDA version if you have NVIDIA GPU
   # Ollama will automatically detect and use GPU
   ```

2. **Choose the right O3 model**:
   - `o3:3b`: Fast responses, good for simple queries
   - `o3:8b`: **Recommended** - Best balance of performance and resources
   - `o3:70b`: Highest quality, best for complex reasoning

3. **Adjust model size** based on your hardware:
   - 3B models: Fast, lower quality
   - 8B models: Good balance
   - 70B models: Best quality, requires more resources

4. **Monitor resource usage**:

   ```bash
   # Check Ollama process
   ps aux | grep ollama
   
   # Monitor memory usage
   htop
   ```

## Troubleshooting

### Common Issues

1. **"Connection refused" or "Cannot connect to Ollama"**
   - Make sure Ollama server is running: `ollama serve`
   - Check if port 11434 is available
   - Verify firewall settings

2. **"Out of memory" errors**
   - Use a smaller model (3B instead of 8B)
   - Close other applications to free RAM
   - Consider upgrading your system RAM

3. **"Model not found"**
   - Download the model: `ollama pull model_name`
   - Check available models: `ollama list`
   - Verify model name in config

4. **Slow response times**
   - Use a smaller model
   - Ensure adequate RAM
   - Consider GPU acceleration
   - Close other resource-intensive applications

### Performance Optimization

1. **GPU Acceleration**:

   ```bash
   # Check if CUDA is available
   nvidia-smi
   
   # Ollama will automatically use GPU if available
   ```

2. **Memory Management**:

   ```bash
   # Monitor memory usage
   free -h
   
   # Clear model cache if needed
   ollama rm model_name
   ollama pull model_name
   ```

3. **Network Configuration**:

   ```bash
   # Check if Ollama is accessible
   curl http://localhost:11434/api/tags
   
   # Test specific model
   curl -X POST http://localhost:11434/api/generate \
     -H "Content-Type: application/json" \
     -d '{"model": "llama3.1:8b", "prompt": "Hello"}'
   ```

## Advanced Configuration

### Custom Model Configuration

Create a custom model configuration:

```bash
# Create a Modelfile
cat > Modelfile << EOF
FROM llama3.1:8b
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER top_k 40
SYSTEM You are a helpful assistant for technical documentation.
EOF

# Create custom model
ollama create my-custom-model -f Modelfile
```

### Environment Variables

Set Ollama-specific environment variables:

```bash
# Set Ollama host (if running on different machine)
export OLLAMA_HOST="http://192.168.1.100:11434"

# Set model cache directory
export OLLAMA_MODELS="/path/to/custom/models"
```

### Docker Setup (Alternative)

If you prefer Docker:

```bash
# Pull Ollama Docker image
docker pull ollama/ollama

# Run Ollama container
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Pull model in container
docker exec -it ollama ollama pull llama3.1:8b
```

## Security Considerations

### Local Deployment Benefits

1. **No API keys required**: All processing happens locally
2. **No data sent to external servers**: Complete privacy
3. **No usage limits**: No rate limiting or token costs
4. **Offline operation**: Works without internet connection

### Best Practices

1. **Keep Ollama updated**:

   ```bash
   # Update Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Monitor system resources**:
   - Check CPU and memory usage
   - Monitor disk space for model storage

3. **Secure network access** (if exposing externally):

   ```bash
   # Only allow local access (default)
   ollama serve
   
   # For external access, use firewall rules
   # and consider authentication
   ```

## Support

- [Ollama Documentation](https://ollama.ai/docs)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Model Library](https://ollama.ai/library)
- [Community Discord](https://discord.gg/ollama)
- [Troubleshooting Guide](https://github.com/ollama/ollama/blob/main/docs/troubleshooting.md)
