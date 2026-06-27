"""Custom exception classes and error handlers."""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class QuranNotesException(Exception):
    """Base exception for Quran Notes application."""
    
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(QuranNotesException):
    """Resource not found exception."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedError(QuranNotesException):
    """Unauthorized access exception."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class ValidationError(QuranNotesException):
    """Validation error exception."""
    
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class RateLimitError(QuranNotesException):
    """Rate limit exceeded exception."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class UploadTooLargeError(QuranNotesException):
    """Uploaded file exceeds configured size limit."""

    def __init__(self, message: str = "Uploaded file too large"):
        super().__init__(message, status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


class UploadEmptyError(QuranNotesException):
    """Uploaded file is empty/zero bytes."""

    def __init__(self, message: str = "Uploaded file is empty"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


async def quran_notes_exception_handler(request: Request, exc: QuranNotesException) -> JSONResponse:
    """Handle custom Quran Notes exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        # Use FastAPI's conventional shape so clients can reliably parse errors.
        # Keep 'error' for backward compatibility with any older clients.
        content={"detail": exc.message, "error": exc.message}
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": "Internal server error"}
    )

