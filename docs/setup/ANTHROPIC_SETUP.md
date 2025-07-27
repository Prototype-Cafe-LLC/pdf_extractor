# Anthropic API Key Setup Guide

## Quick Setup

### 1. Get Your Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in to your account
3. Navigate to "API Keys" section
4. Click "Create Key"
5. Copy your API key (starts with `sk-ant-`)

### 2. Set Environment Variable

#### Option A: Terminal (Temporary)

```bash
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
```

#### Option B: Shell Profile (Permanent)

Add to your shell profile file:

**For bash/zsh:**

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"' >> ~/.bashrc
# or
echo 'export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"' >> ~/.zshrc
```

**For Windows:**

```cmd
setx ANTHROPIC_API_KEY "sk-ant-your-api-key-here"
```

#### Option C: .env File

Create a `.env` file in the project root:

```bash
echo 'ANTHROPIC_API_KEY=sk-ant-your-api-key-here' > .env
```

### 3. Verify Setup

Test that your API key is set:

```bash
echo $ANTHROPIC_API_KEY
```

### 4. Test RAG System

Run the test to verify everything works:

```bash
python test_rag_basic.py
```

## Configuration

Update `config/rag_config.yaml` to use Anthropic:

```yaml
llm:
  type: "anthropic"
  model: "claude-4-opus"  # or "claude-3-sonnet", "claude-3-haiku"
  temperature: 0.1
```

## Available Models

### Claude 4 Models (Latest)

- `claude-4-opus`: Most capable model, best for complex reasoning and analysis
- `claude-4-sonnet`: Balanced performance and cost, good for most tasks
- `claude-4-haiku`: Fastest and most cost-effective, good for simple queries

### Claude 3 Models (Previous Generation)

- `claude-3-opus`: Previous generation, still very capable
- `claude-3-sonnet`: Good balance of performance and cost
- `claude-3-haiku`: Fast and cost-effective

### Model Comparison

| Model | Capability | Speed | Cost | Best For |
|-------|------------|-------|------|----------|
| `claude-4-opus` | Highest | Medium | Highest | Complex analysis, reasoning |
| `claude-4-sonnet` | High | Fast | Medium | General tasks, good balance |
| `claude-4-haiku` | Good | Fastest | Lowest | Simple queries, quick responses |
| `claude-3-opus` | Very High | Medium | High | Complex tasks |
| `claude-3-sonnet` | High | Fast | Medium | General use |
| `claude-3-haiku` | Good | Fastest | Low | Simple tasks |

## Pricing

Anthropic charges per token (input + output):

### Claude 4 Models

- **Claude 4 Opus**: $15.00 per 1M input tokens, $75.00 per 1M output tokens
- **Claude 4 Sonnet**: $3.00 per 1M input tokens, $15.00 per 1M output tokens
- **Claude 4 Haiku**: $0.25 per 1M input tokens, $1.25 per 1M output tokens

### Claude 3 Models

- **Claude 3 Opus**: $15.00 per 1M input tokens, $75.00 per 1M output tokens
- **Claude 3 Sonnet**: $3.00 per 1M input tokens, $15.00 per 1M output tokens
- **Claude 3 Haiku**: $0.25 per 1M input tokens, $1.25 per 1M output tokens

### Cost Optimization Tips

1. **Choose the right model**:
   - Use Claude 4 Haiku for simple queries
   - Use Claude 4 Sonnet for general tasks
   - Use Claude 4 Opus only for complex analysis

2. **Optimize prompts**:
   - Keep prompts concise and specific
   - Use clear instructions to reduce output length

3. **Monitor usage**:
   - Check your usage dashboard regularly
   - Set up billing alerts

## Troubleshooting

### Common Issues

1. **"ANTHROPIC_API_KEY environment variable not set"**
   - Make sure you've set the environment variable
   - Restart your terminal after setting it

2. **"Invalid API key"**
   - Check that your key starts with `sk-ant-`
   - Verify the key is correct in Anthropic Console

3. **"Rate limit exceeded"**
   - Anthropic has rate limits based on your plan
   - Check your usage in the Anthropic Console

### Support

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Anthropic Console](https://console.anthropic.com/)
- [Rate Limits](https://docs.anthropic.com/en/api/rate-limits)
