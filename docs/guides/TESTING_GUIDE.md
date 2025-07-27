# Testing Guide for PDF RAG MCP Server Document Addition Issue

## Issue Summary

When adding multiple PDF documents via the MCP server, only some documents are successfully stored in the database, even though the server reports processing all files successfully.

## Test Scenario

1. Clear the database
2. Add 10 PDF documents
3. List documents - expecting 10 but only 2 are shown

## Setup Instructions

1. **Ensure MCP server is properly configured:**
   ```bash
   # Check config files exist
   ls config/rag_config.yaml config/mcp_config.yaml
   ```

2. **Restart MCP server:**
   - Stop the current MCP server
   - Clear logs: `rm logs/*.log` (if exists)
   - Start fresh MCP server instance

3. **Enable debug logging:**
   ```python
   # In mcp_server_simple.py, change logging level:
   logging.basicConfig(
       level=logging.DEBUG,  # Changed from INFO
       format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
   )
   ```

## Test Steps

1. **Via MCP Client (Claude):**
   ```
   - Clear database
   - Add PDF documents from folder (e.g., ./10_pdfs/)
   - List documents
   - Check if all documents are listed
   ```

2. **Direct Python Test:**
   ```bash
   source .venv/bin/activate
   python test_mcp_scenario.py
   ```

3. **Manual Database Check:**
   ```bash
   python debug_mcp_issue.py
   ```

## What to Look For

1. **In MCP logs:**
   - Look for errors during PDF processing
   - Check if all files report "Successfully added"
   - Note any warnings or exceptions

2. **In the database:**
   - Total chunk count
   - Number of unique documents
   - Document names that were successfully added

## Known Working Documents

These 2 documents are consistently added successfully:
- Quectel_BG95_Series_Hardware_Design_V1.5.pdf
- quectel_bg95bg77bg600l_series_at_commands_manual_v2-0.pdf

## Debugging Tips

1. **Check PDF file validity:**
   ```python
   # Test if PDFs can be opened
   import pymupdf4llm
   for pdf in Path("./10_pdfs").glob("*.pdf"):
       try:
           text = pymupdf4llm.to_markdown(str(pdf))
           print(f"✓ {pdf.name} - OK")
       except Exception as e:
           print(f"✗ {pdf.name} - Error: {e}")
   ```

2. **Monitor memory usage:**
   - Large PDFs might cause memory issues
   - Check system resources during processing

3. **Check file permissions:**
   ```bash
   ls -la ./10_pdfs/*.pdf
   ```

## Expected vs Actual Results

**Expected:** All 10 PDFs added successfully
**Actual:** Only 2 PDFs are in the database

## Log Rotation

To preserve logs for analysis:
```bash
# Before testing
mkdir -p logs/archive
cp logs/*.log logs/archive/test_$(date +%Y%m%d_%H%M%S).log

# After testing
tail -n 1000 logs/mcp_server.log > logs/test_results.log
```