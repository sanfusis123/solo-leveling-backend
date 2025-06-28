from datetime import datetime, timezone

def utc_now() -> datetime:
    """Get current UTC datetime with timezone info"""
    return datetime.now(timezone.utc)