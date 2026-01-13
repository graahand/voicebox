# VoiceBox Logging System Documentation

## Overview
Comprehensive file-based logging system implemented across all VoiceBox modules. Warnings and errors are logged to files without displaying in console (except user-facing error messages).

## Log Files

### Primary Log File
- **Location**: `/logs/voicebox.log`
- **Level**: DEBUG (all messages)
- **Contains**: All log messages from all modules
- **Format**: `YYYY-MM-DD HH:MM:SS - MODULE - LEVEL - MESSAGE`

### Error Log File
- **Location**: `/logs/voicebox_errors.log`
- **Level**: WARNING (warnings and errors only)
- **Contains**: Only warnings and errors with full tracebacks
- **Format**: Same as primary log

## Implementation

### Logger Configuration (`config/logger.py`)
- **VoiceBoxLogger**: Singleton logger manager
- **Features**:
  - Dual-file logging (main + errors)
  - Automatic directory creation
  - Third-party library warning suppression
  - Module-specific loggers
  - Exception tracebacks with `exc_info=True`

### Suppressed Libraries
Third-party warnings/info messages suppressed:
- urllib3
- transformers
- sentence_transformers
- faiss
- librosa
- audioread
- faster_whisper

## Modules Updated

### ✅ main.py
**Logging Points**:
- Application startup/shutdown
- Mode selection (text/voice/hybrid)
- Initialization of all handlers
- User input processing (text preview only)
- Audio recording start/stop
- Audio playback events
- File cleanup operations
- Error handling with tracebacks

**User-Facing Output**:
- Welcome messages and menus (kept visible)
- Input prompts (kept visible)
- Response text (kept visible)
- Error messages (duplicated in logs)

### ✅ modules/llm_handler.py
**Logging Points**:
- Model verification and loading
- RAG initialization (vector/keyword fallback)
- Context retrieval from RAG
- Query processing with response length
- Error generation with tracebacks
- Conversation history usage

### ✅ modules/vector_rag_handler.py
**Logging Points**:
- Embedding model initialization
- Document loading and processing
- Chunk generation (count and sample)
- Embedding generation progress
- FAISS index building
- Search queries and results
- Similarity scores
- Futuruma query detection

### ✅ modules/tts_handler.py
**Logging Points**:
- MeloTTS model initialization
- Speaker validation and fallback
- Audio generation (length, speaker, speed)
- File saving operations
- Error handling

### ✅ modules/stt_handler.py
**Logging Points**:
- Whisper model loading
- Device selection (CUDA/CPU fallback)
- Transcription start/complete
- Language detection
- Segment details
- Audio file validation
- Error handling with tracebacks

### ✅ modules/conversation_manager.py
**Logging Points**:
- Conversation saving (file path, interaction count)
- Conversation loading
- History clearing
- Session ID tracking

### ✅ modules/response_formatter.py
**Status**: Test code only - no runtime logging needed

## Usage Examples

### Basic Logging
```python
from config.logger import get_logger, suppress_library_warnings

# Suppress third-party warnings
suppress_library_warnings()

# Get module-specific logger
logger = get_logger('module_name')

# Log messages
logger.debug("Debug information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error message")
```

### Error Logging with Traceback
```python
try:
    # Some operation
    result = process_data()
except Exception as e:
    logger.error("Operation failed", exc_info=True)
    print(f"Error: {e}")  # User-facing message
```

### Progress Logging
```python
logger.info(f"Processing {count} items...")
for item in items:
    logger.debug(f"Processing item: {item}")
logger.info(f"Processing complete: {count} items processed")
```

## Log Levels

### DEBUG (logs only)
- Detailed diagnostic information
- Function entry/exit
- Parameter values
- Internal state changes

### INFO (logs only)
- General informational messages
- Process milestones
- Successful operations
- Configuration details

### WARNING (logs + errors.log)
- Deprecated features
- Recoverable errors
- Unexpected but handled conditions
- Fallback operations

### ERROR (logs + errors.log)
- Exceptions and failures
- Unrecoverable errors
- Stack traces
- Critical issues

## Benefits

1. **Clean Console**: No library warnings or verbose output
2. **Complete History**: All operations logged with timestamps
3. **Error Tracking**: Full tracebacks in error log
4. **Module Tracing**: Track flow across components
5. **Debug Support**: Detailed information for troubleshooting
6. **Performance Analysis**: Timing and performance metrics
7. **Audit Trail**: Complete record of all interactions

## File Locations

```
test_voicebox/
├── config/
│   └── logger.py          # ✅ Logger configuration
├── logs/
│   ├── voicebox.log       # All messages (DEBUG+)
│   └── voicebox_errors.log # Warnings/errors only
├── modules/
│   ├── llm_handler.py     # ✅ Updated with logging
│   ├── vector_rag_handler.py # ✅ Updated with logging
│   ├── tts_handler.py     # ✅ Updated with logging
│   ├── stt_handler.py     # ✅ Updated with logging
│   ├── conversation_manager.py # ✅ Updated with logging
│   └── response_formatter.py # ✅ No changes needed
├── main.py                # ✅ Updated with logging
└── test_logging.py        # ✅ Test script
```

## Testing

Run the logging test:
```bash
python test_logging.py
```

Check log files:
```bash
# View main log
tail -f logs/voicebox.log

# View error log
tail -f logs/voicebox_errors.log

# View recent errors
grep "ERROR" logs/voicebox.log
```

## Maintenance

### Log Rotation
Consider implementing log rotation for long-running deployments:
- Use Python's `RotatingFileHandler`
- Set max file size (e.g., 10MB)
- Keep 5-10 backup files

### Log Cleanup
Periodically clean old logs:
```bash
# Delete logs older than 30 days
find logs/ -name "*.log" -mtime +30 -delete
```

## Future Enhancements

1. **Structured Logging**: Add JSON format for easier parsing
2. **Remote Logging**: Send logs to centralized service
3. **Log Levels**: Make configurable via config.py
4. **Performance Metrics**: Add timing decorators
5. **User Sessions**: Track user sessions separately

## Summary

✅ **Complete**: All 6 core modules updated with comprehensive logging
✅ **Clean**: Console output limited to user-facing messages only
✅ **Detailed**: Full process tracking in log files
✅ **Errors**: Complete tracebacks in dedicated error log
✅ **Configurable**: Easy to extend and customize
