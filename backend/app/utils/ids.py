"""ID generation utilities."""
import secrets
from datetime import datetime, timezone


def generate_ulid_like_id(prefix: str) -> str:
    """
    Generate a ULID-like ID with a prefix.
    
    Format: {prefix}_{timestamp_base36}_{random}
    Example: sess_01J8X9Z2K3M4N5P6Q7R8S9T0
    
    Args:
        prefix: Prefix for the ID (e.g., 'sess', 'note')
        
    Returns:
        Generated ID string
    """
    # Get current timestamp in milliseconds
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    # Convert to base36 for compactness
    timestamp_b36 = _to_base36(timestamp)
    
    # Generate random component (12 chars)
    random_part = secrets.token_urlsafe(9).replace('-', '').replace('_', '')[:12].upper()
    
    return f"{prefix}_{timestamp_b36}{random_part}"


def _to_base36(num: int) -> str:
    """Convert integer to base36 string."""
    if num == 0:
        return '0'
    
    digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    result = ''
    
    while num > 0:
        result = digits[num % 36] + result
        num //= 36
    
    return result


def generate_session_id() -> str:
    """Generate a session ID."""
    return generate_ulid_like_id("sess")


def generate_note_id() -> str:
    """Generate a note ID."""
    return generate_ulid_like_id("note")


def generate_highlight_id() -> str:
    """Generate a highlight ID."""
    return generate_ulid_like_id("hl")