# Security Best Practices for KeneyApp

## Overview

This document outlines comprehensive security best practices for KeneyApp, covering HIPAA/GDPR compliance, secure coding practices, and operational security.

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Data Protection](#data-protection)
3. [API Security](#api-security)
4. [Input Validation](#input-validation)
5. [Secrets Management](#secrets-management)
6. [Database Security](#database-security)
7. [Network Security](#network-security)
8. [Monitoring & Incident Response](#monitoring--incident-response)
9. [Compliance](#compliance)
10. [Security Checklist](#security-checklist)

## Authentication & Authorization

### JWT Token Security

✅ **Already Implemented:**

- JWT tokens with expiration
- Secure token generation with secrets
- Role-based access control (RBAC)

🔒 **Best Practices:**

```python
# Use strong secret keys (min 32 characters)
import secrets
SECRET_KEY = secrets.token_urlsafe(32)

# Set appropriate token expiration
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Short-lived tokens

# Always validate tokens on protected endpoints
current_user = Depends(get_current_user)
```

### Multi-Factor Authentication (MFA)

✅ **Already Implemented:** TOTP-based MFA

**Setup for Users:**

```python
# Generate MFA secret
import pyotp
secret = pyotp.random_base32()

# Verify MFA token
totp = pyotp.TOTP(secret)
is_valid = totp.verify(user_token)
```

### Session Management

- Implement session timeout (30 minutes recommended)
- Invalidate tokens on logout
- Implement token refresh mechanism (future enhancement)

## Data Protection

### Encryption at Rest

✅ **Already Implemented:** AES-256-GCM encryption for sensitive data

```python
from app.core.encryption import encrypt_field, decrypt_field

# Encrypt sensitive data before storage
encrypted_ssn = encrypt_field(patient_ssn)

# Decrypt when needed
ssn = decrypt_field(encrypted_ssn)
```

### Encryption in Transit

🔒 **Production Requirements:**

- Always use HTTPS/TLS 1.3
- Implement HSTS (HTTP Strict Transport Security)
- Use strong cipher suites only

```python
# Nginx configuration
ssl_protocols TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### Password Security

✅ **Already Implemented:**

- bcrypt hashing with salt
- Minimum password requirements

🔒 **Enforce Strong Passwords:**

```python
import re

def validate_password(password: str) -> bool:
    """
    Password requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False

    patterns = [
        r'[A-Z]',  # Uppercase
        r'[a-z]',  # Lowercase
        r'[0-9]',  # Digit
        r'[!@#$%^&*(),.?":{}|<>]',  # Special char
    ]

    return all(re.search(pattern, password) for pattern in patterns)
```

### Data Sanitization

- Remove sensitive data from logs
- Implement data masking for display
- Sanitize data before deletion (GDPR compliance)

```python
import logging

# Configure logging to exclude sensitive fields
class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        # Remove password, SSN, credit card, etc. from logs
        message = str(record.msg)
        message = re.sub(r'\bpassword\b.*', 'password=***', message, flags=re.IGNORECASE)
        message = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '***-**-****', message)
        record.msg = message
        return True

logging.getLogger().addFilter(SensitiveDataFilter())
```

## API Security

### Rate Limiting

✅ **Already Implemented:** slowapi rate limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply rate limits
@limiter.limit("10/minute")  # Strict for writes
@limiter.limit("100/minute")  # Lenient for reads
```

### CORS Configuration

✅ **Already Implemented:** Configured CORS

🔒 **Production Settings:**

```python
# Be specific with allowed origins in production
ALLOWED_ORIGINS = [
    "https://app.yourdomain.com",
    "https://api.yourdomain.com"
]

# Never use "*" in production!
# allow_origins=["*"]  # ❌ NEVER DO THIS
```

### API Input Validation

✅ **Already Implemented:** Pydantic schemas

```python
from pydantic import BaseModel, EmailStr, Field, validator

class PatientCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., regex=r'^\+?1?\d{9,15}$')

    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        # Prevent SQL injection, XSS
        if not v.replace(' ', '').isalpha():
            raise ValueError('Name must contain only letters')
        return v.strip()
```

### Security Headers

✅ **Already Implemented:** Security headers middleware

```python
# Comprehensive security headers
headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}
```

## Input Validation

### SQL Injection Prevention

✅ **Already Protected:** Using SQLAlchemy ORM

```python
# Good - Parameterized queries via ORM
patient = db.query(Patient).filter(Patient.id == patient_id).first()

# Bad - Never build SQL strings manually
# sql = f"SELECT * FROM patients WHERE id = {patient_id}"  # ❌ VULNERABLE
```

### XSS Prevention

```python
from html import escape

def sanitize_html(text: str) -> str:
    """Remove potentially dangerous HTML/JavaScript."""
    return escape(text)

# Apply to user inputs before storing/displaying
sanitized_notes = sanitize_html(patient_notes)
```

### Path Traversal Prevention

```python
import os
from pathlib import Path

def safe_file_path(filename: str, base_dir: str) -> Path:
    """Prevent directory traversal attacks."""
    base_path = Path(base_dir).resolve()
    file_path = (base_path / filename).resolve()

    # Ensure the file is within base directory
    if not str(file_path).startswith(str(base_path)):
        raise ValueError("Invalid file path")

    return file_path
```

### Command Injection Prevention

```python
import subprocess
import shlex

# Bad - Vulnerable to command injection
# os.system(f"convert {user_file} output.pdf")  # ❌

# Good - Use subprocess with list
subprocess.run(['convert', user_file, 'output.pdf'], check=True)

# Or sanitize input
safe_file = shlex.quote(user_file)
```

## Secrets Management

### Environment Variables

✅ **Already Implemented:** python-dotenv

```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use strong, unique secrets
openssl rand -base64 32  # Generate secret key
```

### Rotating Secrets

```python
# Implement secret rotation strategy
# 1. Update secret in environment
# 2. Deploy with dual secret support
# 3. Monitor for old secret usage
# 4. Remove old secret after transition period

def get_secret_key():
    """Support multiple keys during rotation."""
    primary_key = os.getenv('SECRET_KEY')
    fallback_key = os.getenv('SECRET_KEY_OLD')
    return [primary_key, fallback_key]
```

### Cloud Secrets Management

For production, use dedicated secrets management:

- AWS Secrets Manager
- Azure Key Vault
- Google Secret Manager
- HashiCorp Vault

```python
# Example with AWS Secrets Manager
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']
```

## Database Security

### Connection Security

```python
# Use SSL for database connections in production
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"

# Limit database user permissions
# CREATE USER keneyapp WITH PASSWORD 'strong_password';
# GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO keneyapp;
# REVOKE ALL ON pg_catalog, information_schema FROM keneyapp;
```

### Audit Logging

✅ **Already Implemented:** Comprehensive audit logs

```python
# Log all critical operations
log_audit_event(
    user_id=current_user.id,
    action="CREATE",
    resource_type="patient",
    resource_id=patient.id,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

### Regular Backups

```bash
# Automated PostgreSQL backups
#!/bin/bash
BACKUP_DIR="/backups/keneyapp"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U keneyapp -h localhost keneyapp | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"

# Encrypt backups
gpg --encrypt --recipient backup@company.com "$BACKUP_DIR/backup_$DATE.sql.gz"

# Retain backups for 30 days
find $BACKUP_DIR -mtime +30 -delete
```

## Network Security

### Firewall Configuration

```bash
# Allow only necessary ports
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   # SSH (consider changing default port)
ufw allow 443/tcp  # HTTPS
ufw allow 80/tcp   # HTTP (redirect to HTTPS)
ufw enable

# Limit SSH attempts
ufw limit ssh
```

### DDoS Protection

```nginx
# Nginx rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

location /api/ {
    limit_req zone=api burst=20 nodelay;
}

location /api/v1/auth/login {
    limit_req zone=login burst=3;
}
```

### VPN for Database Access

- Never expose database ports to the internet
- Use VPN or SSH tunnels for remote access
- Implement IP whitelisting

## Monitoring & Incident Response

### Security Monitoring

```python
# Monitor security events
security_events = [
    "failed_login_attempts",
    "unauthorized_access_attempts",
    "suspicious_api_calls",
    "data_export_activities",
    "permission_escalation_attempts"
]

# Alert on threshold
if failed_login_count > 10:
    send_security_alert("Multiple failed login attempts detected")
```

### Intrusion Detection

- Monitor audit logs for suspicious patterns
- Set up alerts for:
  - Multiple failed login attempts
  - Access to sensitive data
  - Unusual API usage patterns
  - Permission changes
  - Database schema changes

### Incident Response Plan

1. **Detection**: Monitor logs and alerts
2. **Containment**: Isolate affected systems
3. **Investigation**: Analyze logs and determine scope
4. **Remediation**: Fix vulnerabilities, patch systems
5. **Recovery**: Restore from backups if needed
6. **Documentation**: Document incident and response
7. **Notification**: Notify affected users (GDPR/HIPAA requirement)

## Compliance

### HIPAA Compliance Checklist

- [x] Access controls (authentication + authorization)
- [x] Audit logs for PHI access
- [x] Data encryption at rest
- [x] Data encryption in transit
- [x] Automatic session timeout
- [x] User activity monitoring
- [ ] Business Associate Agreements (BAA)
- [ ] Regular security training
- [ ] Risk assessments (annual)
- [ ] Breach notification procedures

### GDPR Compliance Checklist

- [x] User consent management
- [x] Right to access (data export)
- [x] Right to erasure (data deletion)
- [x] Data portability
- [x] Audit trails
- [x] Data encryption
- [ ] Privacy by design
- [ ] Data protection impact assessment (DPIA)
- [ ] Data breach notification (within 72 hours)
- [ ] DPO appointment (if required)

## Security Checklist

### Development

- [ ] Use parameterized queries (ORM)
- [ ] Validate all user inputs
- [ ] Implement proper error handling (no sensitive info in errors)
- [ ] Use secure dependencies (check for vulnerabilities)
- [ ] Implement least privilege access
- [ ] Remove debug code before deployment
- [ ] Use static code analysis tools

### Deployment

- [ ] Set DEBUG=False in production
- [ ] Use strong, unique SECRET_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure security headers
- [ ] Set up rate limiting
- [ ] Configure proper CORS
- [ ] Enable audit logging
- [ ] Set up monitoring and alerts
- [ ] Implement automated backups
- [ ] Use secrets management service

### Operations

- [ ] Regular security updates
- [ ] Dependency vulnerability scanning
- [ ] Regular penetration testing
- [ ] Security training for team
- [ ] Incident response plan
- [ ] Regular backup testing
- [ ] Access review (quarterly)
- [ ] Security audit (annual)

## Security Tools

### Static Analysis

```bash
# Python security linting
pip install bandit
bandit -r app/

# Dependency vulnerability scanning
pip install safety
safety check

# SAST scanning
pip install semgrep
semgrep --config=auto app/
```

### Dynamic Analysis

```bash
# OWASP ZAP for web app scanning
docker run -v $(pwd):/zap/wrk/:rw -t owasp/zap2docker-stable \
  zap-baseline.py -t http://localhost:8000 -r report.html

# API security testing
pip install apisecurity
apisecurity scan http://localhost:8000/api/v1/docs
```

### Container Security

```bash
# Scan Docker images
docker scan keneyapp:latest

# Use Trivy
trivy image keneyapp:latest
```

## Resources

### Standards & Frameworks

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/)
- [GDPR](https://gdpr.eu/)

### Tools & Libraries

- [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/)
- [Bandit](https://bandit.readthedocs.io/)
- [Safety](https://pyup.io/safety/)
- [Trivy](https://aquasecurity.github.io/trivy/)
- [OWASP ZAP](https://www.zaproxy.org/)

## Conclusion

Security is an ongoing process, not a one-time implementation. Regularly review and update security practices, stay informed about new vulnerabilities, and conduct periodic security assessments. When in doubt, follow the principle of least privilege and defense in depth.

**Remember:** The cost of prevention is always less than the cost of a breach.
