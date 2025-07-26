#!/usr/bin/env python3
"""Test Japanese query about BG95 position and data transmission."""

import asyncio
from pathlib import Path
from mcp_server_simple import SimplePDFRAGMCPServer


async def test_japanese_query():
    """Test querying the system with a Japanese question."""
    print("Testing Japanese Query for BG95")
    print("=" * 50)
    
    # Create server instance
    server = SimplePDFRAGMCPServer()
    
    # First, check what documents we have
    print("\n1. Checking available documents...")
    result = await server._handle_list_documents()
    print(result.text)
    
    # Query in Japanese about BG95 position acquisition and data transmission
    queries = [
        # Original Japanese query
        "BG95で位置取得とデータ送信を交互に行うためのATコマンドのシーケンスを教えて",
        
        # Same query with keywords for better retrieval
        "BG95 GNSS GPS position location data transmission AT command sequence 位置取得 データ送信 ATコマンド シーケンス",
        
        # English version for comparison
        "What is the AT command sequence for alternating between position acquisition and data transmission on BG95?",
        
        # More specific query
        "BG95 AT+QGPSLOC AT+QISEND sequence for GPS location and TCP data transmission"
    ]
    
    print("\n2. Testing queries...")
    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"Question: {query}")
        print("-" * 40)
        
        result = await server._handle_query({
            "question": query,
            "top_k": 5  # Get more results for better coverage
        })
        
        print(result.text)
        print("\n" + "=" * 50)
    
    # Also test a specific AT command query
    print("\n3. Testing specific AT command queries...")
    specific_queries = [
        "AT+QGPSLOC command usage and parameters",
        "AT+QISEND for TCP data transmission",
        "How to configure GNSS on BG95"
    ]
    
    for query in specific_queries:
        print(f"\nQuery: {query}")
        result = await server._handle_query({
            "question": query,
            "top_k": 3
        })
        print(result.text[:500] + "..." if len(result.text) > 500 else result.text)


async def main():
    """Main entry point."""
    try:
        await test_japanese_query()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set environment variable to avoid tokenizer warnings
    import os
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    asyncio.run(main())