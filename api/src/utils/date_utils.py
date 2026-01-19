"""Date utility functions for API."""
from datetime import datetime
from typing import Union


def convert_date_format(date_str: str) -> str:
    """
    Convert YYYYMMDD format to milliseconds timestamp
    
    Args:
        date_str: Date string in YYYYMMDD format
        
    Returns:
        String representation of milliseconds timestamp
        
    Raises:
        ValueError: If date format is invalid
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        return str(int(date_obj.timestamp() * 1000))
    except ValueError:
        raise ValueError(f"Date format must be YYYYMMDD, got: {date_str}")


def timestamp_to_iso(timestamp: Union[int, float]) -> str:
    """
    Convert milliseconds timestamp to ISO format string
    
    Args:
        timestamp: Timestamp in milliseconds
        
    Returns:
        ISO format datetime string
    """
    return datetime.fromtimestamp(timestamp / 1000).isoformat()
