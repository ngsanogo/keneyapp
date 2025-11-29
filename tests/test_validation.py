"""
Tests for input validation and sanitization
"""
import pytest
from unittest.mock import MagicMock

from app.core.validation import (
    InputSanitizer,
    validate_uuid,
    validate_date_format,
    validate_strong_password,
)


class TestInputSanitizer:
    """Test InputSanitizer utility class"""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization"""
        result = InputSanitizer.sanitize_string("  test string  ")
        assert result == "test string"
    
    def test_sanitize_string_control_chars(self):
        """Test removal of control characters"""
        # Contains control characters
        result = InputSanitizer.sanitize_string("test\x00\x01\x1fstring")
        assert result == "teststring"
        
        # Tab and newline should be preserved
        result = InputSanitizer.sanitize_string("test\tstring\n")
        assert "\t" in result
        assert "\n" in result
    
    def test_sanitize_string_max_length(self):
        """Test truncation to max length"""
        long_string = "a" * 200
        result = InputSanitizer.sanitize_string(long_string, max_length=50)
        assert len(result) == 50
    
    def test_sanitize_html(self):
        """Test HTML tag removal"""
        html = "<script>alert('xss')</script>Hello<b>World</b>"
        result = InputSanitizer.sanitize_html(html)
        assert "<script>" not in result
        assert "<b>" not in result
        assert "Hello" in result
        assert "World" in result
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Remove path components
        result = InputSanitizer.sanitize_filename("../../etc/passwd")
        assert result == "passwd"
        assert ".." not in result
        
        # Remove dangerous characters
        result = InputSanitizer.sanitize_filename("file<>:name.txt")
        assert result == "filename.txt"
        
        # Remove leading dots
        result = InputSanitizer.sanitize_filename(".hidden")
        assert result == "hidden"
    
    def test_sanitize_email(self):
        """Test email sanitization"""
        # Valid email
        result = InputSanitizer.sanitize_email("  Test@Example.COM  ")
        assert result == "test@example.com"
        
        # Invalid email
        with pytest.raises(ValueError, match="Invalid email format"):
            InputSanitizer.sanitize_email("not_an_email")
    
    def test_sanitize_phone(self):
        """Test phone number sanitization"""
        result = InputSanitizer.sanitize_phone("+33 1 23 45 67 89")
        assert result == "+33 1 23 45 67 89"
        
        # Remove letters
        result = InputSanitizer.sanitize_phone("+33 (0)1 abc 23-45")
        assert "abc" not in result
        assert "+" in result
        assert "-" in result
    
    def test_sanitize_url(self):
        """Test URL sanitization"""
        # Valid HTTP URL
        result = InputSanitizer.sanitize_url("https://example.com/path")
        assert result == "https://example.com/path"
        
        # Dangerous protocol
        with pytest.raises(ValueError, match="Dangerous protocol"):
            InputSanitizer.sanitize_url("javascript:alert('xss')")
        
        with pytest.raises(ValueError, match="Dangerous protocol"):
            InputSanitizer.sanitize_url("data:text/html,<script>alert('xss')</script>")
        
        # Non-HTTP protocol
        with pytest.raises(ValueError, match="Only HTTP/HTTPS protocols allowed"):
            InputSanitizer.sanitize_url("ftp://example.com")


class TestValidationFunctions:
    """Test standalone validation functions"""
    
    def test_validate_uuid(self):
        """Test UUID validation"""
        # Valid UUIDs
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        assert validate_uuid("550E8400-E29B-41D4-A716-446655440000")  # Uppercase
        
        # Invalid UUIDs
        assert not validate_uuid("not-a-uuid")
        assert not validate_uuid("550e8400-e29b-41d4-a716")  # Too short
        assert not validate_uuid("550e8400e29b41d4a716446655440000")  # No hyphens
    
    def test_validate_date_format(self):
        """Test date format validation"""
        # Valid dates
        assert validate_date_format("2024-01-15")
        assert validate_date_format("2024-12-31")
        
        # Invalid dates
        assert not validate_date_format("2024-13-01")  # Invalid month
        assert not validate_date_format("2024-01-32")  # Invalid day
        assert not validate_date_format("01/15/2024")  # Wrong format
        assert not validate_date_format("not-a-date")
    
    def test_validate_date_format_custom(self):
        """Test custom date format validation"""
        assert validate_date_format("15/01/2024", format="%d/%m/%Y")
        assert validate_date_format("01-15-2024", format="%m-%d-%Y")
    
    def test_validate_strong_password(self):
        """Test password strength validation"""
        # Strong password
        is_valid, violations = validate_strong_password("Str0ng!Pass")
        assert is_valid
        assert len(violations) == 0
        
        # Too short
        is_valid, violations = validate_strong_password("Short1!")
        assert not is_valid
        assert "at least 8 characters" in violations[0]
        
        # No uppercase
        is_valid, violations = validate_strong_password("lowercase123!")
        assert not is_valid
        assert "uppercase letter" in violations[0]
        
        # No lowercase
        is_valid, violations = validate_strong_password("UPPERCASE123!")
        assert not is_valid
        assert "lowercase letter" in violations[0]
        
        # No digit
        is_valid, violations = validate_strong_password("NoDigit!Pass")
        assert not is_valid
        assert "digit" in violations[0]
        
        # No special character
        is_valid, violations = validate_strong_password("NoSpecial123")
        assert not is_valid
        assert "special character" in violations[0]
        
        # Multiple violations
        is_valid, violations = validate_strong_password("weak")
        assert not is_valid
        assert len(violations) > 1


class TestSQLInjectionPrevention:
    """Test SQL injection prevention patterns"""
    
    def test_sql_patterns_detected(self):
        """Test that common SQL injection patterns would be detected"""
        from app.core.validation import RequestValidationMiddleware
        
        middleware = RequestValidationMiddleware(app=MagicMock())
        
        # Common SQL injection patterns
        sql_patterns = [
            "' OR 1=1--",
            "'; DROP TABLE users--",
            "1' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 'a'='a",
        ]
        
        for pattern in sql_patterns:
            # Check if pattern would match SQL injection regex
            matched = any(
                regex.search(pattern) 
                for regex in middleware.sql_regex
            )
            assert matched, f"SQL pattern not detected: {pattern}"


class TestXSSPrevention:
    """Test XSS prevention patterns"""
    
    def test_xss_patterns_detected(self):
        """Test that common XSS patterns would be detected"""
        from app.core.validation import RequestValidationMiddleware
        
        middleware = RequestValidationMiddleware(app=MagicMock())
        
        # Common XSS patterns
        xss_patterns = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='javascript:alert()'></iframe>",
            "<body onload=alert('xss')>",
        ]
        
        for pattern in xss_patterns:
            matched = any(
                regex.search(pattern) 
                for regex in middleware.xss_regex
            )
            assert matched, f"XSS pattern not detected: {pattern}"


class TestPathTraversalPrevention:
    """Test path traversal prevention"""
    
    def test_path_traversal_detected(self):
        """Test that path traversal attempts would be detected"""
        from app.core.validation import RequestValidationMiddleware
        
        middleware = RequestValidationMiddleware(app=MagicMock())
        
        # Path traversal patterns
        traversal_patterns = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "%2e%2e%2f",
            "....//....//",
        ]
        
        for pattern in traversal_patterns:
            matched = any(
                regex.search(pattern) 
                for regex in middleware.path_regex
            )
            assert matched, f"Path traversal not detected: {pattern}"
