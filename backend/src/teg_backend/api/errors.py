from __future__ import annotations

from fastapi import HTTPException

from ..application.game_service import ServiceError
from ..domain.enums import ErrorCode

_STATUS = {
    ErrorCode.AUTH_FAILED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.INVALID_ACTION: 409,
    ErrorCode.GAME_STATE_CONFLICT: 409,
    ErrorCode.NOT_YOUR_TURN: 409,
    ErrorCode.GAME_NOT_RUNNING: 409,
    ErrorCode.INVALID_PAYLOAD: 422,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.MESSAGE_TOO_LARGE: 413,
}


def to_http(exc: ServiceError) -> HTTPException:
    return HTTPException(
        status_code=_STATUS.get(exc.code, 400),
        detail={"code": exc.code, "message": exc.message},
    )
