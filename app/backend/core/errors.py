"""HTTP error helpers."""

from fastapi import HTTPException, status


class AppError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def raise_http(exc: AppError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)
