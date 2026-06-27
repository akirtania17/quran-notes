"""FastAPI dependencies."""
from fastapi import Header, HTTPException


async def get_client_id(x_client_id: str = Header(..., alias="X-Client-Id")) -> str:
    """
    Extract and validate X-Client-Id header.
    
    Args:
        x_client_id: Client ID from header
        
    Returns:
        Validated client ID
        
    Raises:
        HTTPException: If client ID is missing or invalid
    """
    if not x_client_id or len(x_client_id.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="X-Client-Id header is required"
        )
    
    # Basic validation - ensure reasonable length
    if len(x_client_id) > 100:
        raise HTTPException(
            status_code=400,
            detail="X-Client-Id header is too long"
        )
    
    return x_client_id.strip()

