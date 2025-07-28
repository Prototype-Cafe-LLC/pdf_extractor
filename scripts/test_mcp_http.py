#!/usr/bin/env python3
"""Test MCP HTTP endpoints.

This script tests the MCP protocol endpoints on the HTTP server.
"""

import json
import requests
import sys
from pathlib import Path

# Default server URL
SERVER_URL = "http://localhost:8080"


def test_mcp_initialize():
    """Test MCP initialization."""
    print("Testing MCP initialization...")
    
    response = requests.post(
        f"{SERVER_URL}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Initialization successful")
        print(f"  Protocol version: {data['result']['protocolVersion']}")
        print(f"  Server: {data['result']['serverInfo']['name']} v{data['result']['serverInfo']['version']}")
        return True
    else:
        print(f"✗ Initialization failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False


def test_mcp_list_tools():
    """Test listing MCP tools."""
    print("\nTesting MCP tools listing...")
    
    response = requests.post(
        f"{SERVER_URL}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if 'error' in data:
            print(f"✗ Tools listing error: {data['error']}")
            return False
        tools = data['result']['tools']
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        return True
    else:
        print(f"✗ Tools listing failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False


def test_mcp_call_tool():
    """Test calling an MCP tool."""
    print("\nTesting MCP tool call (get_system_info)...")
    
    response = requests.post(
        f"{SERVER_URL}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_system_info",
                "arguments": {}
            }
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if 'result' in data and 'content' in data['result']:
            print("✓ Tool call successful:")
            for content in data['result']['content']:
                if content['type'] == 'text':
                    # Print first few lines of the response
                    lines = content['text'].split('\n')[:10]
                    for line in lines:
                        print(f"  {line}")
                    if len(content['text'].split('\n')) > 10:
                        print("  ...")
        return True
    else:
        print(f"✗ Tool call failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False


def test_health_check():
    """Test basic health check."""
    print("Testing server health...")
    
    try:
        response = requests.get(f"{SERVER_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Server is {data['status']}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to server: {e}")
        return False


def main():
    """Run all tests."""
    print(f"Testing MCP HTTP endpoints on {SERVER_URL}")
    print("=" * 50)
    
    # First check if server is running
    if not test_health_check():
        print("\nPlease ensure the HTTP server is running:")
        print("  python -m src.mcp.http_server")
        sys.exit(1)
    
    # Test MCP endpoints
    tests_passed = 0
    total_tests = 3
    
    if test_mcp_initialize():
        tests_passed += 1
    
    if test_mcp_list_tools():
        tests_passed += 1
    
    if test_mcp_call_tool():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n✓ All MCP HTTP tests passed!")
        print("\nYou can now configure Claude Desktop to use:")
        print(f'  "url": "{SERVER_URL}/mcp"')
    else:
        print("\n✗ Some tests failed. Please check the server logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()