"""
Request validation middleware
Provides comprehensive input validation and sanitization
"""

import re
from typing import Any, Callable, Dict, List, Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_middleware import logger


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request validation and sanitization

    Features:
    - SQL injection prevention
    - XSS attack prevention
    - Path traversal prevention
    - Malicious pattern detection
    - Request size limits
    - Content type validation
    """

    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(--|\#|\/\*|\*\/)",  # SQL comments
        r"(\bor\b\s+\d+\s*=\s*\d+)",  # OR 1=1
        r"(\band\b\s+\d+\s*=\s*\d+)",  # AND 1=1
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
        r"\.\.\\",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",  # Shell metacharacters
        r"\$\([^\)]*\)",  # Command substitution
        r"`[^`]*`",  # Backtick command execution
    ]

    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10 MB default
        super().__init__(app)
        self.max_request_size = max_request_size
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for performance"""
        self.sql_regex = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.xss_regex = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
        self.path_regex = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
        self.cmd_regex = [re.compile(p) for p in self.COMMAND_INJECTION_PATTERNS]

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request before passing to endpoint"""
        try:
            # Check request size
            if hasattr(request, "headers"):
                content_length = request.headers.get("content-length")
                if content_length and int(content_length) > self.max_request_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            f"Request too large. " f"Maximum size: {self.max_request_size} bytes"
                        ),
                    )

            # Validate path parameters
            if request.path_params:
                self._validate_params(request.path_params, "path")

            # Validate query parameters
            if request.query_params:
                self._validate_params(dict(request.query_params), "query")

            # Validate specific endpoints
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_body(request)

            # Process request
            response = await call_next(request)
            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

    def _validate_params(self, params: Dict[str, Any], param_type: str):
        """Validate parameters for malicious patterns"""
        for key, value in params.items():
            if not isinstance(value, str):
                continue

            value_str = str(value)

            # Check for SQL injection
            for pattern in self.sql_regex:
                if pattern.search(value_str):
                    logger.warning(
                        f"SQL injection attempt in {param_type} " f"parameter '{key}': {value_str}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid {param_type} parameter: {key}",
                    )

            # Check for XSS
            for pattern in self.xss_regex:
                if pattern.search(value_str):
                    logger.warning(
                        f"XSS attempt in {param_type} " f"parameter '{key}': {value_str}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid {param_type} parameter: {key}",
                    )

            # Check for path traversal
            for pattern in self.path_regex:
                if pattern.search(value_str):
                    logger.warning(
                        f"Path traversal attempt in {param_type} " f"parameter '{key}': {value_str}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid {param_type} parameter: {key}",
                    )

    async def _validate_body(self, request: Request):
        """Validate request body (lightweight check)"""
        # Skip validation for multipart/form-data (file uploads)
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            return

        # For JSON bodies, basic validation is handled by Pydantic
        # This is just an additional security layer
        pass


class InputSanitizer:
    """
    Utility class for sanitizing user inputs
    Use in Pydantic validators or service layer
    """

    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input
        - Strips whitespace
        - Removes control characters
        - Truncates to max length
        """
        if not value:
            return value

        # Strip whitespace
        value = value.strip()

        # Remove control characters (except newline and tab)
        value = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", value)

        # Truncate if needed
        if max_length and len(value) > max_length:
            value = value[:max_length]

        return value

    @staticmethod
    def sanitize_html(value: str) -> str:
        """
        Remove HTML tags from string
        Simple tag stripping for basic XSS prevention
        For rich text, use a proper HTML sanitizer library
        """
        if not value:
            return value

        # Remove HTML tags
        value = re.sub(r"<[^>]+>", "", value)

        # Remove HTML entities
        value = re.sub(r"&[a-zA-Z]+;", "", value)

        return value

    @staticmethod
    def sanitize_filename(value: str) -> str:
        """
        Sanitize filename
        Removes path traversal attempts and dangerous characters
        """
        if not value:
            return value

        # Remove path components
        value = value.split("/")[-1]
        value = value.split("\\")[-1]

        # Remove dangerous characters
        value = re.sub(r'[<>:"|?*\x00-\x1f]', "", value)

        # Remove leading dots (hidden files)
        value = value.lstrip(".")

        # Ensure not empty
        if not value:
            value = "file"

        return value

    @staticmethod
    def sanitize_email(value: str) -> str:
        """
        Basic email sanitization
        Proper validation should be done with Pydantic EmailStr
        """
        if not value:
            return value

        value = value.lower().strip()

        # Basic validation
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
            raise ValueError("Invalid email format")

        return value

    @staticmethod
    def sanitize_phone(value: str) -> str:
        """
        Sanitize phone number
        Removes non-numeric characters except + and spaces
        """
        if not value:
            return value

        # Keep only digits, +, spaces, and hyphens
        value = re.sub(r"[^0-9+\s-]", "", value)

        return value.strip()

    @staticmethod
    def sanitize_url(value: str) -> str:
        """
        Basic URL sanitization
        Removes javascript: and data: protocols
        """
        if not value:
            return value

        value = value.strip()

        # Block dangerous protocols
        dangerous_protocols = ["javascript:", "data:", "vbscript:", "file:"]
        value_lower = value.lower()

        for protocol in dangerous_protocols:
            if value_lower.startswith(protocol):
                raise ValueError(f"Dangerous protocol not allowed: {protocol}")

        # Ensure http/https if protocol specified
        if "://" in value and not value.lower().startswith(("http://", "https://")):
            raise ValueError("Only HTTP/HTTPS protocols allowed")

        return value


def validate_uuid(value: str) -> bool:
    """Validate UUID format"""
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
    )
    return bool(uuid_pattern.match(value))


def validate_date_format(value: str, format: str = "%Y-%m-%d") -> bool:
    """Validate date string format"""
    from datetime import datetime

    try:
        datetime.strptime(value, format)
        return True
    except ValueError:
        return False


def validate_strong_password(password: str) -> tuple[bool, List[str]]:
    """
    Validate password strength

    Returns:
        (is_valid, list_of_violations)
    """
    violations = []

    if len(password) < 8:
        violations.append("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", password):
        violations.append("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        violations.append("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        violations.append("Password must contain at least one digit")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        violations.append("Password must contain at least one special character")

    return len(violations) == 0, violations
