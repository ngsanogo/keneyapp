# Security Policy

## Overview

KeneyApp takes security seriously. As a healthcare data management platform, we handle sensitive patient information and comply with GDPR and HIPAA regulations. This document outlines our security policies and procedures.

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | ✅ Yes             |
| 1.x     | ✅ Yes             |
| < 1.0   | ❌ No              |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please report it by emailing:

📧 **<contact@isdataconsulting.com>**

### What to Include in Your Report

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** of the vulnerability
- **Possible fix** (if you have one)
- **Your contact information** for follow-up

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Status Updates**: Every 7 days until resolved
- **Fix Timeline**: Critical issues within 7 days, others based on severity

### After Reporting

1. We will acknowledge receipt of your report
2. We will investigate and validate the vulnerability
3. We will work on a fix and notify you of progress
4. Once fixed, we will publicly disclose the vulnerability (crediting you if desired)
5. You may be eligible for recognition in our security acknowledgments

## Security Features

### Authentication & Authorization

- ✅ **JWT-based authentication** with secure token management
- ✅ **OAuth2/OIDC support** for SSO (Google, Microsoft, Okta)
- ✅ **Role-Based Access Control (RBAC)** with granular permissions
- ✅ **Bootstrap guardrails**: configurable default admin account for test/demo environments (disable in production)
- ✅ **Password hashing** using bcrypt with strong work factors
- ✅ **Multi-Factor Authentication (MFA)** support with TOTP
- ✅ **Session management** with secure cookie settings
- ✅ **Account lockout** after failed login attempts

### Data Protection

- ✅ **Data encryption at rest** using AES-256-GCM
- ✅ **TLS/SSL encryption in transit** (HTTPS only)
- ✅ **Database encryption** for sensitive fields
- ✅ **Secure password storage** with bcrypt
- ✅ **API key encryption** in database
- ✅ **Backup encryption** for data backups

### API Security

- ✅ **Input validation** using Pydantic schemas
- ✅ **SQL injection prevention** with parameterized queries
- ✅ **XSS protection** with output encoding
- ✅ **CSRF protection** with token validation
- ✅ **Rate limiting** to prevent abuse (100 requests/minute per IP)
- ✅ **CORS configuration** with allowed origins
- ✅ **Security headers** (CSP, X-Frame-Options, etc.)

### Monitoring & Logging

- ✅ **Comprehensive audit logging** for all sensitive operations
- ✅ **Failed authentication tracking**
- ✅ **Anomaly detection** for suspicious activities
- ✅ **Access logging** with IP addresses and user agents
- ✅ **Security event monitoring** with Prometheus metrics

### Infrastructure Security

- ✅ **Container security** with minimal base images
- ✅ **Network segmentation** in Kubernetes
- ✅ **Secrets management** using Kubernetes secrets
- ✅ **Regular security updates** for dependencies
- ✅ **Automated vulnerability scanning**

## Security Best Practices for Contributors

### Code Security

1. **Never commit secrets** to version control
   - Use environment variables
   - Use `.env.example` as a template
   - Add `.env` to `.gitignore`

2. **Validate all inputs**

   ```python
   from pydantic import BaseModel, validator

   class PatientCreate(BaseModel):
       first_name: str
       email: EmailStr

       @validator('first_name')
       def validate_name(cls, v):
           if not v or len(v) < 2:
               raise ValueError('Name must be at least 2 characters')
           return v
   ```

3. **Use parameterized queries**

   ```python
   # Good - prevents SQL injection
   patient = db.query(Patient).filter(Patient.id == patient_id).first()

   # Bad - vulnerable to SQL injection
   db.execute(f"SELECT * FROM patients WHERE id = {patient_id}")
   ```

4. **Sanitize output**

   ```python
   from html import escape
   safe_text = escape(user_input)
   ```

5. **Use secure random generators**

   ```python
   import secrets
   token = secrets.token_urlsafe(32)
   ```

### Dependency Management

1. **Keep dependencies up to date**

   ```bash
   # Backend
   pip install --upgrade -r requirements.txt
   pip-audit

   # Frontend
   npm update
   npm audit fix
   ```

2. **Review dependency changes**
   - Check changelogs for breaking changes
   - Review security advisories
   - Test thoroughly after updates

3. **Use lock files**
   - `requirements.txt` for Python (with pinned versions)
   - `package-lock.json` for Node.js

### Environment Variables

Never store sensitive data in code. Use environment variables:

```bash
# .env (never commit this file!)
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=strong-and-unique-32-char-secret
ENCRYPTION_SALT=rotation-friendly-unique-salt
TOKEN_ISSUER=keneyapp
TOKEN_AUDIENCE=keneyapp-clients
DATABASE_URL=postgresql://user:password@localhost/db
REDIS_URL=redis://localhost:6379
```

#### JWT hardening

- Tokens now carry `iss`, `aud`, and `iat` claims and are validated on every request. Configure `TOKEN_ISSUER` and `TOKEN_AUDIENCE` to match your deployment, and rotate `SECRET_KEY` when required.

#### Encryption hardening

- Provide an `ENCRYPTION_KEY` that is distinct from `SECRET_KEY` in production and at least 32 characters long. Use `ENCRYPTION_SALT` to scope derived keys per environment or rotation event.

### Secure Configuration

1. **Disable debug mode in production**

   ```python
   DEBUG = False
   ```

2. **Use HTTPS only**

   ```python
   # FastAPI - force HTTPS
   from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
   app.add_middleware(HTTPSRedirectMiddleware)
   ```

3. **Set secure cookie flags**

   ```python
   response.set_cookie(
       key="session",
       value=token,
       httponly=True,
       secure=True,
       samesite="strict"
   )
   ```

4. **Configure CORS properly**

   ```python
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Never use "*"
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

## Compliance

### GDPR Compliance

- ✅ **Data minimization** - collect only necessary data
- ✅ **Right to erasure** - users can delete their data
- ✅ **Data portability** - users can export their data
- ✅ **Consent management** - explicit opt-in for data processing
- ✅ **Breach notification** - automated alerts for security incidents
- ✅ **Privacy by design** - security built into development process

### HIPAA Compliance

- ✅ **Access controls** - role-based access to PHI
- ✅ **Audit trails** - comprehensive logging of PHI access
- ✅ **Encryption** - at rest and in transit
- ✅ **Authentication** - secure user authentication
- ✅ **Data integrity** - validation and checksums
- ✅ **Automatic logoff** - session timeout after inactivity

## Security Checklist for Deployments

Before deploying to production, ensure:

- [ ] All secrets are stored in environment variables or secret managers
- [ ] HTTPS/TLS is enabled with valid certificates
- [ ] Debug mode is disabled
- [ ] Database backups are encrypted and automated
- [ ] Rate limiting is configured
- [ ] CORS is properly configured (no wildcards)
- [ ] Security headers are enabled
- [ ] Dependencies are up to date
- [ ] Audit logging is enabled
- [ ] Monitoring and alerting are configured
- [ ] Firewall rules are properly configured
- [ ] SSH access is restricted and key-based only
- [ ] Default passwords are changed
- [ ] Unnecessary services are disabled
- [ ] Security scanning tools are running

## Security Tools

We use the following tools to maintain security:

### Automated Scanning

- **GitHub Dependabot** - Dependency vulnerability scanning
- **CodeQL** - Static code analysis for security issues
- **npm audit** - Frontend dependency vulnerabilities
- **pip-audit** - Backend dependency vulnerabilities
- **OWASP ZAP** - Web application security testing
- **Snyk** - Container and dependency scanning

### Manual Reviews

- Code reviews for all pull requests
- Security-focused code reviews for sensitive changes
- Periodic security audits
- Penetration testing (annual)

## Security Updates

### Dependency Updates

We regularly update dependencies to patch security vulnerabilities:

```bash
# Check for vulnerabilities
npm audit
pip-audit

# Update dependencies
npm update
pip install --upgrade -r requirements.txt
```

### Security Patches

- **Critical**: Released within 24-48 hours
- **High**: Released within 7 days
- **Medium**: Included in next regular release
- **Low**: Included in next major release

## Resources

### Security Guidelines

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

### Healthcare Security

- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [GDPR](https://gdpr.eu/)
- [HL7 FHIR Security](https://www.hl7.org/fhir/security.html)

## Contact

For security concerns or questions:

📧 **<contact@isdataconsulting.com>**

For urgent security issues, please use the vulnerability reporting process described above.

---

**Last Updated**: October 2024

This security policy is regularly reviewed and updated to reflect current best practices and regulatory requirements.
