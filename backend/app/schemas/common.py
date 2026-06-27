"""Common schemas shared across endpoints."""
from typing import Optional


class PaginatedResponse:
    """Base class for paginated responses."""
    
    next_offset: Optional[int] = None

