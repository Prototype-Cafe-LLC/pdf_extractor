#!/usr/bin/env python3
"""Setup and test the RAG system with PDF documents."""

import asyncio
from pathlib import Path

from mcp_server_simple import SimplePDFRAGMCPServer


async def setup_and_test():
    """Setup RAG system and test with questions."""
    print("RAG System Setup and Test")
    print("=" * 50)

    # Create server instance
    server = SimplePDFRAGMCPServer()

    # Step 1: Check current documents
    print("\n1. Checking current documents in knowledge base...")
    result = await server._handle_list_documents()
    print(result.text)

    # Step 2: Add test PDFs if available
    print("\n2. Looking for PDF files to add...")
    pdf_dirs = [
        Path("test/resources/pdf"),
        Path("md"),  # Already converted markdown files
        Path("."),
    ]

    pdf_files = []
    for pdf_dir in pdf_dirs:
        if pdf_dir.exists():
            pdf_files.extend(list(pdf_dir.glob("*.pdf")))

    if not pdf_files:
        print("No PDF files found. Let's check if we have markdown files in 'md' directory...")
        md_dir = Path("md")
        if md_dir.exists():
            md_files = list(md_dir.glob("*.md"))
            print(f"Found {len(md_files)} markdown files:")
            for md_file in md_files[:5]:  # Show first 5
                print(f"  - {md_file.name}")

            # Note: The current system expects PDFs, not markdown files
            print("\nNote: The system currently expects PDF files to add to the knowledge base.")
            print("The markdown files in 'md' directory are the converted outputs.")
            print("\nTo query these documents, you would need to:")
            print("1. Use the original PDF files from test/resources/pdf/")
            print("2. Or modify the RAG system to accept markdown files directly")

    # Try to add PDFs
    if pdf_files:
        print(f"\nFound {len(pdf_files)} PDF files. Adding first 3...")
        for i, pdf_file in enumerate(pdf_files[:3]):
            print(f"\nAdding {pdf_file.name}...")
            result = await server._handle_add_document(
                {"pdf_path": str(pdf_file), "document_type": "technical_manual"}
            )
            print(result.text)

    # Step 3: List documents after adding
    print("\n3. Listing documents after adding...")
    result = await server._handle_list_documents()
    print(result.text)

    # Step 4: Test some queries
    print("\n4. Testing queries...")

    test_queries = [
        "What is the AT+CSQ command used for?",
        "How do I check signal quality?",
        "What are the power requirements for BG95?",
        "Explain the TCP/IP functionality",
        "What is the purpose of MUX mode?",
    ]

    for query in test_queries[:3]:  # Test first 3 queries
        print(f"\nQuery: {query}")
        result = await server._handle_query({"question": query, "top_k": 3})
        print(result.text)
        print("-" * 40)

    # Step 5: Show how to use with MCP
    print("\n5. Using with MCP Server")
    print("=" * 50)
    print("\nTo use this with Claude Desktop or other MCP clients:")
    print("1. Start the MCP server: python mcp_server_simple.py")
    print("2. Configure your MCP client to connect to the server")
    print("3. Use the available tools:")
    print("   - query_technical_docs: Ask questions about the documentation")
    print("   - add_pdf_document: Add new PDF documents")
    print("   - list_documents: See what's in the knowledge base")
    print("   - get_system_info: Check system status")


async def main():
    """Main entry point."""
    try:
        await setup_and_test()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
