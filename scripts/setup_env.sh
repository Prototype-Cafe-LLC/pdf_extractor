#!/bin/bash
# Setup script for PDF RAG MCP Server

echo "PDF RAG MCP Server Environment Setup"
echo "===================================="
echo ""

# Check current LLM configuration
llm_type=$(grep -A1 "llm:" config/rag_config.yaml | grep "type:" | awk '{print $2}' | tr -d '"')
echo "Current LLM configuration: $llm_type"
echo ""

# Provide instructions based on configuration
case "$llm_type" in
    "openai")
        echo "To use OpenAI, you need to set OPENAI_API_KEY:"
        echo "  export OPENAI_API_KEY='your-api-key-here'"
        echo ""
        echo "Or add it to your .env file:"
        echo "  echo 'OPENAI_API_KEY=your-api-key-here' >> .env"
        ;;
    "anthropic")
        echo "To use Anthropic Claude, you need to set ANTHROPIC_API_KEY:"
        echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
        echo ""
        echo "Or add it to your .env file:"
        echo "  echo 'ANTHROPIC_API_KEY=your-api-key-here' >> .env"
        ;;
    "ollama")
        echo "For Ollama, make sure Ollama is running locally:"
        echo "  ollama serve"
        echo ""
        echo "Then pull the model specified in config:"
        model=$(grep -A2 "llm:" config/rag_config.yaml | grep "model:" | awk '{print $2}' | tr -d '"')
        echo "  ollama pull $model"
        ;;
    *)
        echo "Unknown LLM type: $llm_type"
        ;;
esac

echo ""
echo "Note: The LLM will only be initialized when you make a query."
echo "Other operations (list_documents, add_pdf_document) will work without API keys."