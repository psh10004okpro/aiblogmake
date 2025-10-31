"""
Global error handlers for FastAPI.

이 모듈은 FastAPI 애플리케이션의 전역 에러 핸들러를 정의합니다.
모든 예외를 일관된 형식으로 변환하여 사용자 친화적인 응답을 제공합니다.
"""

from typing import Union, Dict, Any
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import traceback

from app.core.exceptions import BlogAutomationException
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 500,
    details: Dict[str, Any] = None,
    request_id: str = None,
    path: str = None
) -> JSONResponse:
    """
    Create standardized error response.

    Args:
        error_code: 에러 코드
        message: 사용자 친화적 메시지
        status_code: HTTP 상태 코드
        details: 추가 상세 정보
        request_id: 요청 ID (추적용)
        path: 요청 경로

    Returns:
        JSONResponse: 표준화된 에러 응답
    """
    error_response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }

    # 추가 상세 정보
    if details:
        error_response["error"]["details"] = details

    # 요청 ID (로그 추적용)
    if request_id:
        error_response["error"]["request_id"] = request_id

    # 요청 경로
    if path:
        error_response["error"]["path"] = path

    # 개발 모드에서만 스택 트레이스 포함
    if settings.debug and details and "traceback" in details:
        error_response["error"]["traceback"] = details["traceback"]

    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def blog_automation_exception_handler(
    request: Request,
    exc: BlogAutomationException
) -> JSONResponse:
    """
    Handle custom BlogAutomationException.

    우리가 정의한 커스텀 예외를 처리합니다.
    """
    logger.error(
        "blog_automation_exception",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
        details=exc.details
    )

    return create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle HTTP exceptions (4xx, 5xx).

    FastAPI/Starlette의 HTTPException을 처리합니다.
    """
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )

    # 한글 에러 메시지 매핑
    korean_messages = {
        400: "잘못된 요청입니다.",
        401: "인증이 필요합니다.",
        403: "접근 권한이 없습니다.",
        404: "요청한 리소스를 찾을 수 없습니다.",
        405: "허용되지 않는 메서드입니다.",
        409: "요청이 충돌합니다.",
        422: "입력 데이터가 올바르지 않습니다.",
        429: "요청 횟수 제한을 초과했습니다.",
        500: "서버 내부 오류가 발생했습니다.",
        502: "외부 서비스 연결에 실패했습니다.",
        503: "서비스를 일시적으로 사용할 수 없습니다.",
        504: "요청 시간이 초과되었습니다.",
    }

    message = korean_messages.get(exc.status_code, str(exc.detail))

    return create_error_response(
        error_code=f"HTTP_{exc.status_code}",
        message=message,
        status_code=exc.status_code,
        details={"original_detail": str(exc.detail)} if settings.debug else None,
        path=request.url.path
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    요청 데이터 검증 실패를 처리합니다.
    """
    errors = []

    # Pydantic 에러를 사용자 친화적으로 변환
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        error_type = error["type"]
        message = error["msg"]

        # 한글 에러 메시지 변환
        korean_message = translate_validation_error(error_type, message, field)

        errors.append({
            "field": field,
            "message": korean_message,
            "type": error_type
        })

    logger.warning(
        "validation_error",
        path=request.url.path,
        errors=errors
    )

    return create_error_response(
        error_code="VALIDATION_ERROR",
        message="입력 데이터가 올바르지 않습니다. 아래 필드를 확인해주세요.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": errors},
        path=request.url.path
    )


def translate_validation_error(error_type: str, message: str, field: str) -> str:
    """
    Translate Pydantic validation errors to Korean.

    Args:
        error_type: Pydantic 에러 타입
        message: 원본 메시지
        field: 필드 이름

    Returns:
        str: 한글 에러 메시지
    """
    translations = {
        "value_error.missing": f"{field}은(는) 필수 항목입니다.",
        "type_error.integer": f"{field}은(는) 정수여야 합니다.",
        "type_error.float": f"{field}은(는) 숫자여야 합니다.",
        "type_error.string": f"{field}은(는) 문자열이어야 합니다.",
        "type_error.boolean": f"{field}은(는) true 또는 false여야 합니다.",
        "type_error.list": f"{field}은(는) 목록이어야 합니다.",
        "type_error.dict": f"{field}은(는) 객체여야 합니다.",
        "value_error.any_str.min_length": f"{field}의 길이가 너무 짧습니다.",
        "value_error.any_str.max_length": f"{field}의 길이가 너무 깁니다.",
        "value_error.number.not_ge": f"{field}의 값이 너무 작습니다.",
        "value_error.number.not_le": f"{field}의 값이 너무 큽니다.",
        "value_error.email": f"{field}이(가) 올바른 이메일 형식이 아닙니다.",
        "value_error.url": f"{field}이(가) 올바른 URL 형식이 아닙니다.",
        "value_error.datetime": f"{field}이(가) 올바른 날짜/시간 형식이 아닙니다.",
    }

    # 에러 타입에 맞는 번역 찾기
    for key, translation in translations.items():
        if error_type.startswith(key):
            return translation

    # 기본 메시지
    return f"{field}: {message}"


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.

    데이터베이스 관련 에러를 처리합니다.
    """
    logger.error(
        "database_error",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path
    )

    # IntegrityError (중복, 외래키 위반 등)
    if isinstance(exc, IntegrityError):
        return create_error_response(
            error_code="DB_003",
            message="데이터 무결성 오류가 발생했습니다. 중복된 데이터이거나 잘못된 참조입니다.",
            status_code=status.HTTP_409_CONFLICT,
            details={"error": str(exc)} if settings.debug else None,
            path=request.url.path
        )

    # 일반 데이터베이스 오류
    return create_error_response(
        error_code="DB_ERROR",
        message="데이터베이스 오류가 발생했습니다. 관리자에게 문의해주세요.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"error": str(exc)} if settings.debug else None,
        path=request.url.path
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle all uncaught exceptions.

    처리되지 않은 모든 예외를 처리합니다.
    """
    # 스택 트레이스 로깅
    tb = traceback.format_exc()

    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        traceback=tb
    )

    # 사용자 친화적 메시지
    user_message = "예기치 않은 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    details = None
    if settings.debug:
        details = {
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": tb.split("\n")
        }

    return create_error_response(
        error_code="INTERNAL_ERROR",
        message=user_message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
        path=request.url.path
    )


# 에러 코드별 한글 도움말
ERROR_CODE_HELP = {
    "KEYWORD_001": "Google Ads API 설정 가이드: https://developers.google.com/google-ads/api",
    "KEYWORD_002": "네이버 검색광고 API 가이드: https://naver.github.io/searchad-apidoc/",
    "CONTENT_001": "Claude API 크레딧을 확인하세요: https://console.anthropic.com",
    "IMAGE_001": "OpenAI API 크레딧을 확인하세요: https://platform.openai.com/usage",
    "IMAGE_002": "Unsplash API 제한을 확인하세요: https://unsplash.com/developers",
    "PUBLISH_001": "WordPress REST API가 활성화되어 있는지 확인하세요.",
    "PUBLISH_002": "WordPress 애플리케이션 비밀번호를 새로 발급받으세요.",
    "DB_001": "데이터베이스 연결 정보를 확인하세요 (.env 파일의 DATABASE_URL)",
    "CONFIG_001": ".env 파일에 필요한 API 키를 설정했는지 확인하세요.",
}


def get_error_help(error_code: str) -> str:
    """
    Get help message for error code.

    Args:
        error_code: 에러 코드

    Returns:
        str: 도움말 메시지
    """
    return ERROR_CODE_HELP.get(error_code, "자세한 내용은 로그를 확인하거나 관리자에게 문의하세요.")
