#!/usr/bin/env python3
"""
Test script to verify logging system works correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config.logger import get_logger, suppress_library_warnings

# Suppress third-party library warnings
suppress_library_warnings()

logger = get_logger('test_logging')

def test_logging():
    """Test different log levels."""
    print("Testing VoiceBox logging system...")
    print("Check logs in:")
    print("  - logs/voicebox.log (all messages)")
    print("  - logs/voicebox_errors.log (warnings and errors only)")
    print()
    
    logger.debug("This is a DEBUG message (only in voicebox.log)")
    logger.info("This is an INFO message (only in voicebox.log)")
    logger.warning("This is a WARNING message (in both log files)")
    logger.error("This is an ERROR message (in both log files)")
    
    try:
        # Simulate an error
        result = 1 / 0
    except Exception as e:
        logger.error("This is an ERROR with traceback", exc_info=True)
    
    print("\nLogging test complete!")
    print("Logs should be written to:")
    print("  - logs/voicebox.log")
    print("  - logs/voicebox_errors.log")

if __name__ == "__main__":
    test_logging()
