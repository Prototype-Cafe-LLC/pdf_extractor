#!/usr/bin/env python3
"""Test script for log rotation functionality.

This script tests the rotating log handler implementation by:
1. Generating log messages to trigger rotation
2. Verifying backup files are created
3. Checking log file size limits
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp.logging_config import configure_mcp_logging, log_system_info


def test_log_rotation():
    """Test log rotation functionality."""
    print("Testing log rotation functionality...")
    
    # Configure logger with small max_bytes for testing
    os.environ['MCP_LOG_MAX_BYTES'] = '1024'  # 1KB for quick rotation
    os.environ['MCP_LOG_BACKUP_COUNT'] = '3'
    os.environ['MCP_LOG_LEVEL'] = 'DEBUG'
    
    # Create logger
    logger = configure_mcp_logging(server_type="test", enable_console=True)
    
    # Log system info
    log_system_info(logger)
    
    # Get log directory
    project_root = Path(__file__).parent.parent
    log_dir = project_root / "logs"
    log_file = log_dir / "test_server.log"
    
    print(f"\nLog directory: {log_dir}")
    print(f"Log file: {log_file}")
    
    # Generate log messages to trigger rotation
    print("\nGenerating log messages to trigger rotation...")
    for i in range(100):
        logger.info(f"Test message {i}: " + "A" * 50)
        logger.debug(f"Debug message {i}: " + "B" * 50)
        logger.warning(f"Warning message {i}: " + "C" * 50)
        
        if i % 10 == 0:
            print(f"  Generated {i+1} sets of messages...")
    
    # Wait a moment for file operations
    time.sleep(0.5)
    
    # Check for rotated files
    print("\nChecking for rotated log files:")
    log_files = sorted(log_dir.glob("test_server.log*"))
    
    for log_file in log_files:
        size = log_file.stat().st_size
        print(f"  {log_file.name}: {size:,} bytes")
    
    # Verify rotation occurred
    backup_files = [f for f in log_files if f.name != "test_server.log"]
    if backup_files:
        print(f"\n✅ Log rotation successful! Found {len(backup_files)} backup files.")
    else:
        print("\n❌ No backup files found. Log rotation may not have been triggered.")
    
    # Test with different log levels
    print("\nTesting different log levels:")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")
    
    # Test exception logging
    print("\nTesting exception logging:")
    try:
        raise ValueError("Test exception for logging")
    except Exception as e:
        logger.error("Caught exception", exc_info=True)
    
    print("\n✅ Log rotation test completed!")
    print(f"Check the log files in: {log_dir}")


def cleanup_test_logs():
    """Clean up test log files."""
    project_root = Path(__file__).parent.parent
    log_dir = project_root / "logs"
    
    # Remove test log files
    for log_file in log_dir.glob("test_server.log*"):
        try:
            log_file.unlink()
            print(f"Removed: {log_file}")
        except Exception as e:
            print(f"Failed to remove {log_file}: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test log rotation")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test logs")
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_test_logs()
    else:
        test_log_rotation()