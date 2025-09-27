import time
import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from functools import wraps

logger = logging.getLogger(__name__)

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def timing_decorator(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"{func.__name__} completed in {format_duration(duration)}")
            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"{func.__name__} failed after {format_duration(duration)}: {str(e)}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"{func.__name__} completed in {format_duration(duration)}")
            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"{func.__name__} failed after {format_duration(duration)}: {str(e)}")
            raise
    
    return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper

def validate_request_data(domain: str, data_format: str, num_records: int) -> Dict[str, str]:
    """Validate request parameters"""
    errors = {}
    
    # Validate domain
    from config import SUPPORTED_DOMAINS
    if domain not in SUPPORTED_DOMAINS:
        errors['domain'] = f"Unsupported domain. Supported: {list(SUPPORTED_DOMAINS.keys())}"
    
    # Validate data format
    from config import SUPPORTED_FORMATS
    if data_format not in SUPPORTED_FORMATS:
        errors['data_format'] = f"Unsupported format. Supported: {list(SUPPORTED_FORMATS.keys())}"
    
    # Validate num_records
    if not isinstance(num_records, int) or num_records < 1 or num_records > 1000:
        errors['num_records'] = "Number of records must be between 1 and 1000"
    
    return errors

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove invalid characters"""
    import re
    # Remove invalid characters for filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Trim underscores from start/end
    sanitized = sanitized.strip('_')
    return sanitized

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def calculate_progress(current: int, total: int) -> float:
    """Calculate progress percentage"""
    if total == 0:
        return 0.0
    return min(100.0, (current / total) * 100)

def estimate_completion_time(start_time: datetime, current_progress: float) -> str:
    """Estimate completion time based on current progress"""
    if current_progress <= 0:
        return "Unknown"
    
    elapsed = datetime.now() - start_time
    total_estimated = elapsed / (current_progress / 100)
    remaining = total_estimated - elapsed
    
    if remaining.total_seconds() < 60:
        return f"{int(remaining.total_seconds())} seconds"
    else:
        minutes = int(remaining.total_seconds() / 60)
        return f"{minutes} minutes"

def safe_json_serialize(obj: Any) -> Any:
    """Safely serialize object for JSON, handling non-serializable types"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, timedelta):
        return obj.total_seconds()
    elif hasattr(obj, '__dict__'):
        return {k: safe_json_serialize(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, (list, tuple)):
        return [safe_json_serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: safe_json_serialize(v) for k, v in obj.items()}
    else:
        return obj

def get_file_extension(data_format: str) -> str:
    """Get appropriate file extension for data format"""
    extensions = {
        "qna": "csv",
        "entity_relationships": "csv",
        "rag_chunks": "csv",
        "fine_tuning": "csv"
    }
    return extensions.get(data_format, "csv")