# OpenAI API Key Setup Guide

## Quick Setup

### 1. Get Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to "API Keys" section
4. Click "Create new secret key"
5. Copy your API key (starts with `sk-`)

### 2. Set Environment Variable

#### Option A: Terminal (Temporary)

```bash
export OPENAI_API_KEY="sk-your-openai-api-key-here"
```

#### Option B: Shell Profile (Permanent)

Add to your shell profile file:

**For bash/zsh:**

```bash
echo 'export OPENAI_API_KEY="sk-your-openai-api-key-here"' >> ~/.bashrc
# or
echo 'export OPENAI_API_KEY="sk-your-openai-api-key-here"' >> ~/.zshrc
```

**For Windows:**

```cmd
setx OPENAI_API_KEY "sk-your-openai-api-key-here"
```

#### Option C: .env File

Create a `.env` file in the project root:

```bash
echo 'OPENAI_API_KEY=sk-your-openai-api-key-here' > .env
```

### 3. Verify Setup

Test that your API key is set:

```bash
echo $OPENAI_API_KEY
```

### 4. Test RAG System

Run the test to verify everything works:

```bash
python test_rag_basic.py
```

## Configuration

Update `config/rag_config.yaml` to use OpenAI:

```yaml
llm:
  type: "openai"
  model: "gpt-4"  # or "gpt-3.5-turbo"
  temperature: 0.1
```

## Available Models

### GPT-4 Models

- `gpt-4`: Most capable model, best for complex reasoning
- `gpt-4-turbo`: Faster and more cost-effective
- `gpt-4o`: Latest model with improved performance

### GPT-3.5 Models

- `gpt-3.5-turbo`: Good balance of performance and cost
- `gpt-3.5-turbo-instruct`: Optimized for instruction following

## Pricing

OpenAI charges per token (input + output):

- **GPT-4**: ~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens
- **GPT-4 Turbo**: ~$0.01 per 1K input tokens, ~$0.03 per 1K output tokens
- **GPT-3.5 Turbo**: ~$0.001 per 1K input tokens, ~$0.002 per 1K output tokens

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY environment variable not set"**
   - Make sure you've set the environment variable
   - Restart your terminal after setting it

2. **"Invalid API key"**
   - Check that your key starts with `sk-`
   - Verify the key is correct in OpenAI Platform

3. **"Rate limit exceeded"**
   - OpenAI has rate limits based on your plan
   - Check your usage in the OpenAI Platform

4. **"Insufficient credits"**
   - Add billing information to your OpenAI account
   - Check your credit balance in the platform

### Rate Limits

- **Free tier**: 3 requests per minute
- **Pay-as-you-go**: 3,500 requests per minute
- **Team/Enterprise**: Higher limits available

## Best Practices

### Cost Optimization

1. **Use appropriate models**:
   - GPT-3.5 Turbo for simple queries
   - GPT-4 for complex reasoning

2. **Optimize prompts**:
   - Keep prompts concise
   - Use clear, specific instructions

3. **Monitor usage**:
   - Check your usage dashboard regularly
   - Set up billing alerts

### Security

1. **Never commit API keys**:
   - Use environment variables
   - Add `.env` to `.gitignore`

2. **Rotate keys regularly**:
   - Create new keys periodically
   - Delete old unused keys

3. **Monitor usage**:
   - Check for unexpected usage patterns
   - Set up usage alerts

## Support

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Platform](https://platform.openai.com/)
- [API Reference](https://platform.openai.com/docs/api-reference)
- [Rate Limits](https://platform.openai.com/docs/guides/rate-limits)
- [Pricing](https://openai.com/pricing)
