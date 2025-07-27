# Privacy Policy

## Overview

This document outlines the privacy and data usage policies for the RAG + LLM MCP
server system, including how data is handled by different model providers and our
local processing pipeline.

## Data Usage Policies by Model Provider

### Claude 4 Opus (Anthropic)

**Official Policy:**

- **Training Data**: Anthropic does NOT use customer data to train their models
- **API Usage**: Data sent via API is not used for training
- **Privacy**: Data is processed for the specific request and not retained for
  training
- **Documentation**: [Anthropic Privacy Policy](https://www.anthropic.com/privacy)

**What Gets Sent:**

- Your specific query
- Retrieved context chunks from your documents
- No raw PDFs or full documents
- No personal or sensitive data (unless in your query)

### O3 Models (Ollama)

**Local Deployment Benefits:**

- **No Data Transmission**: Data never leaves your local machine
- **No Training**: Local models are pre-trained and don't learn from your queries
- **Complete Privacy**: All processing happens locally
- **No External Servers**: No data sent to any cloud services

**What Gets Sent:**

- Nothing leaves your machine
- All processing happens locally

### OpenAI Models (GPT-4, GPT-4o)

**Official Policy:**

- **Training Data**: OpenAI does NOT use customer data to train models
- **API Usage**: Data sent via API is not used for training
- **Retention**: Data may be retained for abuse prevention but not for training
- **Documentation**: [OpenAI Data Usage Policy](https://platform.openai.com/docs/data-usage)

**What Gets Sent:**

- Your specific query
- Retrieved context chunks from your documents
- No raw PDFs or full documents
- No personal or sensitive data (unless in your query)

## How Our RAG System Works

### Data Flow

1. **PDF Processing**:
   - PDFs are converted to markdown locally
   - No data sent to external services during extraction
   - Uses `pymupdf4llm` for local processing

2. **Embedding Generation**:
   - Uses `sentence-transformers/all-MiniLM-L6-v2`
   - Runs locally, no data sent to external services
   - Embeddings stored in local ChromaDB

3. **Query Processing**:
   - Your query is converted to embeddings locally
   - Similar chunks are retrieved from local vector database
   - Only the retrieved context + your query is sent to the LLM

### Local Data Storage

**What We Store Locally:**

- **PDF files**: Original PDFs (if you choose to keep them)
- **Markdown files**: Converted markdown versions
- **Document chunks**: Text chunks with metadata
- **Embeddings**: Vector representations of chunks
- **Vector database**: ChromaDB with all document data

**What We DON'T Store:**

- Your queries (unless you configure logging)
- Personal information
- Sensitive data (unless in your documents)

## Privacy Comparison

| Aspect | Claude 4 Opus | O3 Models |
|--------|---------------|-----------|
| **Data Training** | ❌ No | ❌ No |
| **Data Transmission** | ✅ Yes (query + context) | ❌ No |
| **Data Retention** | ⚠️ Limited (abuse prevention) | ❌ No |
| **Local Processing** | ❌ No | ✅ Yes |
| **Privacy Level** | Medium | Maximum |

## Security Best Practices

### For Cloud Models (Claude 4 Opus, GPT-4)

1. **Review your queries**: Don't send sensitive information in queries
2. **Use context filtering**: Only send relevant document sections
3. **Monitor usage**: Check what data is being sent
4. **Consider data classification**: Don't send classified/proprietary data
5. **Rotate API keys**: For enhanced security
6. **Set billing alerts**: Monitor usage and costs

### For Local Models (O3)

1. **Secure your machine**: Local security is your responsibility
2. **Network isolation**: Keep Ollama server local if needed
3. **Regular updates**: Keep Ollama and models updated
4. **Access control**: Control who can access your local setup
5. **Monitor system resources**: Check CPU and memory usage
6. **Backup your data**: Protect your local document database

## Data Retention and Deletion

### Local Data

**What We Keep:**

- Document embeddings and chunks (for querying)
- Configuration files
- Log files (if enabled)

**How to Delete:**

```bash
# Remove all local data
rm -rf data/
rm -rf config/
```

**What Gets Deleted:**

- All document chunks and embeddings
- Vector database
- Configuration settings
- Log files

### Cloud Provider Data

**Anthropic/OpenAI:**

- We don't control their data retention
- Contact providers directly for data deletion requests
- Typically limited retention for abuse prevention only

## Compliance Considerations

### GDPR Compliance

**Local Processing (O3):**

- ✅ Full GDPR compliance
- ✅ Data never leaves your jurisdiction
- ✅ Complete control over data

**Cloud Processing (Claude 4 Opus, GPT-4):**

- ⚠️ Depends on provider compliance
- ⚠️ Data may cross international borders
- ⚠️ Limited control over data retention

### HIPAA Compliance

**Local Processing (O3):**

- ✅ Can be HIPAA compliant with proper setup
- ✅ No external data transmission
- ✅ Complete control over security

**Cloud Processing (Claude 4 Opus, GPT-4):**

- ❌ Not recommended for HIPAA data
- ❌ Data transmission to external servers
- ❌ Limited control over data handling

### SOX Compliance

**Local Processing (O3):**

- ✅ Can be SOX compliant with proper controls
- ✅ Audit trail can be maintained locally
- ✅ No external dependencies

**Cloud Processing (Claude 4 Opus, GPT-4):**

- ⚠️ Requires careful consideration
- ⚠️ External data transmission
- ⚠️ Limited audit control

## Recommendations by Use Case

### Maximum Privacy Requirements

**Recommended**: O3 Models

- **Why**: Complete local processing
- **Best for**: Sensitive documents, proprietary information, compliance requirements
- **Setup**: Local Ollama installation

### Performance Requirements

**Recommended**: Claude 4 Opus

- **Why**: Best reasoning capabilities
- **Best for**: Complex analysis, research, when privacy isn't critical
- **Setup**: Anthropic API key

### Cost Optimization

**Recommended**: O3 Models

- **Why**: No ongoing costs
- **Best for**: High-volume processing, budget-conscious users
- **Setup**: Local Ollama installation

### Hybrid Approach

**Recommended**: O3 for most queries + Claude 4 Opus for complex analysis

- **Why**: Balance of cost, privacy, and performance
- **Best for**: Organizations with mixed requirements
- **Setup**: Both local and cloud configurations

## Monitoring and Auditing

### Local Monitoring

**What to Monitor:**

- System resource usage (CPU, memory, storage)
- Query patterns and frequency
- Model performance and accuracy
- Security access logs

**Tools:**

```bash
# Monitor system resources
htop
ps aux | grep ollama

# Check storage usage
du -sh data/
df -h

# Monitor network (if applicable)
netstat -tulpn | grep 11434
```

### Cloud Monitoring

**What to Monitor:**

- API usage and costs
- Rate limits and quotas
- Response times and quality
- Data transmission logs

**Tools:**

- Provider dashboards (Anthropic Console, OpenAI Platform)
- Billing alerts and notifications
- Usage analytics and reports

## Incident Response

### Data Breach Procedures

**For Local Systems:**

1. **Immediate Actions**:
   - Stop all services
   - Isolate affected systems
   - Document the incident

2. **Investigation**:
   - Review access logs
   - Identify affected data
   - Assess impact scope

3. **Recovery**:
   - Restore from backups
   - Update security measures
   - Monitor for recurrence

**For Cloud Systems:**

1. **Immediate Actions**:
   - Revoke API keys
   - Contact provider support
   - Document the incident

2. **Investigation**:
   - Review provider logs
   - Identify affected data
   - Assess impact scope

3. **Recovery**:
   - Generate new API keys
   - Update security measures
   - Monitor for recurrence

## Contact Information

### For Privacy Concerns

**Local System Issues:**

- Review this privacy policy
- Check system logs and configuration
- Contact your system administrator

**Cloud Provider Issues:**

- **Anthropic**: [Privacy Policy](https://www.anthropic.com/privacy)
- **OpenAI**: [Data Usage Policy](https://platform.openai.com/docs/data-usage)
- **Ollama**: [GitHub Issues](https://github.com/ollama/ollama/issues)

### For Technical Support

**System Documentation:**

- [RAG README](RAG_README.md)
- [Setup Guides](ANTHROPIC_SETUP.md, [OPENAI_SETUP.md](OPENAI_SETUP.md), [OLLAMA_SETUP.md](OLLAMA_SETUP.md))
- [Model Comparison](MODEL_COMPARISON.md)

## Updates to This Policy

This privacy policy may be updated periodically to reflect:

- Changes in model provider policies
- Updates to our system architecture
- New compliance requirements
- User feedback and concerns

**Last Updated**: December 2024
**Version**: 1.0

## Summary

**Key Points:**

- **None of the models use your data for training**
- **O3 models provide maximum privacy** (local processing only)
- **Cloud models transmit minimal data** (query + context only)
- **Our RAG system is designed to minimize data exposure**
- **Choose based on your privacy requirements vs. performance needs**

**Recommendation**: Use O3 models for maximum privacy, Claude 4 Opus for best
performance, or a hybrid approach for balanced requirements.
