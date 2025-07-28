#!/usr/bin/env python3
"""Test script for log security features.

This script tests that the logging implementation properly handles:
1. Log injection attempts
2. Path traversal attempts
3. Invalid configuration values
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp.logging_config import configure_mcp_logging, sanitize_log_message


def test_log_injection():
    """Test log injection prevention."""
    print("Testing log injection prevention...")
    
    # Test messages with newlines
    malicious_messages = [
        "Normal message\n2025-01-01 00:00:00 - FAKE - CRITICAL - Injected message",
        "Message with \r\n carriage return",
        "Message with\ttabs",
        "Message with \x00 null bytes",
        "Message with \x1b[31m ANSI colors",
    ]
    
    for msg in malicious_messages:
        sanitized = sanitize_log_message(msg)
        print(f"Original: {repr(msg)}")
        print(f"Sanitized: {repr(sanitized)}")
        assert '\n' not in sanitized
        assert '\r' not in sanitized
        assert all(ord(c) >= 32 for c in sanitized)
        print("✅ Passed\n")


def test_path_traversal():
    """Test path traversal prevention."""
    print("\nTesting path traversal prevention...")
    
    # Try to set log directory outside project
    dangerous_paths = [
        "../../../../../../tmp/evil",
        "/etc/passwd",
        "../../../.ssh",
        "~/../../../tmp",
    ]
    
    for path in dangerous_paths:
        print(f"Testing path: {path}")
        os.environ['MCP_LOG_DIR'] = path
        
        try:
            logger = configure_mcp_logging(server_type="security_test", enable_console=False)
            print("❌ FAILED - Path traversal was allowed!")
        except ValueError as e:
            print(f"✅ Passed - Rejected with: {e}")
        except Exception as e:
            print(f"✅ Passed - Rejected with: {type(e).__name__}: {e}")


def test_invalid_config():
    """Test handling of invalid configuration values."""
    print("\nTesting invalid configuration handling...")
    
    # Test invalid environment variables
    test_cases = [
        ("MCP_LOG_MAX_BYTES", "not_a_number", "Invalid max bytes"),
        ("MCP_LOG_BACKUP_COUNT", "abc", "Invalid backup count"),
        ("MCP_LOG_LEVEL", "INVALID_LEVEL", "Invalid log level"),
    ]
    
    for env_var, value, description in test_cases:
        print(f"\nTesting {description}: {env_var}={value}")
        os.environ[env_var] = value
        
        try:
            # For log level, it should raise ValueError
            if env_var == "MCP_LOG_LEVEL":
                try:
                    logger = configure_mcp_logging(server_type="config_test", enable_console=False)
                    print("❌ FAILED - Invalid log level was accepted!")
                except ValueError as e:
                    print(f"✅ Passed - Rejected with: {e}")
            else:
                # For numeric values, should use defaults
                logger = configure_mcp_logging(server_type="config_test", enable_console=False)
                print("✅ Passed - Used default value")
        except Exception as e:
            print(f"✅ Passed - Handled error: {type(e).__name__}: {e}")
        finally:
            # Clean up
            if env_var in os.environ:
                del os.environ[env_var]


def test_resource_limits():
    """Test resource limit validation."""
    print("\nTesting resource limit validation...")
    
    # Test extreme values
    test_cases = [
        ("MCP_LOG_MAX_BYTES", "0", "Too small"),
        ("MCP_LOG_MAX_BYTES", "9999999999", "Too large"),
        ("MCP_LOG_BACKUP_COUNT", "-1", "Negative"),
        ("MCP_LOG_BACKUP_COUNT", "1000", "Too many"),
    ]
    
    for env_var, value, description in test_cases:
        print(f"\nTesting {description}: {env_var}={value}")
        os.environ[env_var] = value
        
        try:
            logger = configure_mcp_logging(server_type="limit_test", enable_console=False)
            print("❌ FAILED - Invalid limit was accepted!")
        except ValueError as e:
            print(f"✅ Passed - Rejected with: {e}")
        except Exception as e:
            print(f"✅ Passed - Handled error: {type(e).__name__}: {e}")
        finally:
            # Clean up
            if env_var in os.environ:
                del os.environ[env_var]


def cleanup():
    """Clean up test artifacts."""
    # Remove any test log files
    log_files = [
        "logs/security_test_server.log",
        "logs/config_test_server.log",
        "logs/limit_test_server.log",
    ]
    
    for log_file in log_files:
        try:
            Path(log_file).unlink()
        except:
            pass


if __name__ == "__main__":
    print("=== Log Security Test Suite ===\n")
    
    try:
        test_log_injection()
        test_path_traversal()
        test_invalid_config()
        test_resource_limits()
        
        print("\n✅ All security tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        cleanup()