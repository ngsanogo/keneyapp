#!/usr/bin/env bash
# validate_env.sh - Environment validation script for KeneyApp
# This script validates that all required environment variables are set and secure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

echo "========================================="
echo "KeneyApp Environment Validation"
echo "========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ ERROR: .env file not found${NC}"
    echo "  Please create a .env file from .env.example"
    exit 1
fi

# Function to check if a variable is set
check_required_var() {
    local var_name=$1
    local var_value=$(grep "^${var_name}=" .env 2>/dev/null | cut -d '=' -f2- | tr -d ' "'"'"'')
    
    if [ -z "$var_value" ]; then
        echo -e "${RED}❌ ERROR: ${var_name} is not set${NC}"
        ((ERRORS++))
        return 1
    else
        echo -e "${GREEN}✅ ${var_name} is set${NC}"
        return 0
    fi
}

# Function to check if a variable uses a secure value (not default/example)
check_secure_var() {
    local var_name=$1
    local insecure_patterns=$2
    local var_value=$(grep "^${var_name}=" .env 2>/dev/null | cut -d '=' -f2- | tr -d ' "'"'"'')
    
    if [ -z "$var_value" ]; then
        return 0  # Already checked by check_required_var
    fi
    
    for pattern in $insecure_patterns; do
        if [[ "$var_value" == *"$pattern"* ]]; then
            echo -e "${YELLOW}⚠️  WARNING: ${var_name} contains potentially insecure value: '$pattern'${NC}"
            echo "   Please use a strong, unique value in production"
            ((WARNINGS++))
            return 1
        fi
    done
    
    return 0
}

# Function to check variable length (for secrets)
check_var_length() {
    local var_name=$1
    local min_length=$2
    local var_value=$(grep "^${var_name}=" .env 2>/dev/null | cut -d '=' -f2- | tr -d ' "'"'"'')
    
    if [ -n "$var_value" ] && [ ${#var_value} -lt $min_length ]; then
        echo -e "${YELLOW}⚠️  WARNING: ${var_name} is too short (< ${min_length} characters)${NC}"
        echo "   Consider using a longer, more secure value"
        ((WARNINGS++))
        return 1
    fi
    
    return 0
}

echo "1. Checking Core Application Settings..."
echo "----------------------------------------"
check_required_var "APP_NAME"
check_required_var "APP_VERSION"
check_required_var "DEBUG"
check_required_var "ENVIRONMENT"

# Check if DEBUG is False in production
ENVIRONMENT=$(grep "^ENVIRONMENT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' "'"'"'')
DEBUG=$(grep "^DEBUG=" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' "'"'"'')

if [ "$ENVIRONMENT" == "production" ] && [ "$DEBUG" != "False" ] && [ "$DEBUG" != "false" ] && [ "$DEBUG" != "0" ]; then
    echo -e "${RED}❌ ERROR: DEBUG must be False in production${NC}"
    ((ERRORS++))
fi

echo ""
echo "2. Checking Security Settings..."
echo "----------------------------------------"
check_required_var "SECRET_KEY"
check_secure_var "SECRET_KEY" "changeme change-me example test"
check_var_length "SECRET_KEY" 32

check_required_var "ALGORITHM"
check_required_var "ACCESS_TOKEN_EXPIRE_MINUTES"

# Check encryption key
check_required_var "ENCRYPTION_KEY"
check_secure_var "ENCRYPTION_KEY" "changeme change-me example test"
check_var_length "ENCRYPTION_KEY" 32

echo ""
echo "3. Checking Database Configuration..."
echo "----------------------------------------"
check_required_var "DATABASE_URL"

# Check if using default database credentials
DB_URL=$(grep "^DATABASE_URL=" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' "'"'"'')
if [[ "$DB_URL" == *"postgres:postgres"* ]] || [[ "$DB_URL" == *":password@"* ]]; then
    echo -e "${YELLOW}⚠️  WARNING: Database URL contains default credentials${NC}"
    echo "   Use strong, unique credentials in production"
    ((WARNINGS++))
fi

echo ""
echo "4. Checking Redis Configuration..."
echo "----------------------------------------"
check_required_var "REDIS_HOST"
check_required_var "REDIS_PORT"
check_required_var "REDIS_PASSWORD"
check_secure_var "REDIS_PASSWORD" "changeme change-me password"

echo ""
echo "5. Checking Celery Configuration..."
echo "----------------------------------------"
check_required_var "CELERY_BROKER_URL"
check_required_var "CELERY_RESULT_BACKEND"

echo ""
echo "6. Checking CORS & Security Headers..."
echo "----------------------------------------"
check_required_var "ALLOWED_ORIGINS"

# Check if using wildcard CORS in production
ALLOWED_ORIGINS=$(grep "^ALLOWED_ORIGINS=" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' "'"'"'')
if [ "$ENVIRONMENT" == "production" ] && [[ "$ALLOWED_ORIGINS" == *"*"* ]]; then
    echo -e "${RED}❌ ERROR: ALLOWED_ORIGINS should not use wildcard (*) in production${NC}"
    ((ERRORS++))
fi

echo ""
echo "7. Checking Optional SMTP Configuration..."
echo "----------------------------------------"
if grep -q "^SMTP_HOST=" .env 2>/dev/null; then
    check_required_var "SMTP_HOST"
    check_required_var "SMTP_PORT"
    check_required_var "SMTP_USER"
    check_required_var "SMTP_PASSWORD"
    check_required_var "SMTP_FROM"
else
    echo -e "${YELLOW}ℹ️  SMTP not configured (optional)${NC}"
fi

echo ""
echo "8. Checking Optional OAuth Configuration..."
echo "----------------------------------------"
if grep -q "^GOOGLE_CLIENT_ID=" .env 2>/dev/null; then
    check_required_var "GOOGLE_CLIENT_ID"
    check_required_var "GOOGLE_CLIENT_SECRET"
else
    echo -e "${YELLOW}ℹ️  Google OAuth not configured (optional)${NC}"
fi

if grep -q "^MICROSOFT_CLIENT_ID=" .env 2>/dev/null; then
    check_required_var "MICROSOFT_CLIENT_ID"
    check_required_var "MICROSOFT_CLIENT_SECRET"
else
    echo -e "${YELLOW}ℹ️  Microsoft OAuth not configured (optional)${NC}"
fi

echo ""
echo "9. Checking File Upload Configuration..."
echo "----------------------------------------"
check_required_var "DOCUMENTS_UPLOAD_DIR"
check_required_var "MAX_DOCUMENT_SIZE"

echo ""
echo "10. Security Best Practices Check..."
echo "----------------------------------------"

# Check if using HTTP in production
if [ "$ENVIRONMENT" == "production" ] && [[ "$ALLOWED_ORIGINS" == *"http://"* ]]; then
    echo -e "${YELLOW}⚠️  WARNING: ALLOWED_ORIGINS contains HTTP URLs${NC}"
    echo "   Use HTTPS in production"
    ((WARNINGS++))
fi

# Check if .env is in .gitignore
if [ -f .gitignore ]; then
    if ! grep -q "^\.env$" .gitignore; then
        echo -e "${RED}❌ ERROR: .env is not in .gitignore${NC}"
        echo "   Add .env to .gitignore to prevent committing secrets"
        ((ERRORS++))
    else
        echo -e "${GREEN}✅ .env is properly ignored by git${NC}"
    fi
fi

# Check file permissions
ENV_PERMS=$(stat -f "%A" .env 2>/dev/null || stat -c "%a" .env 2>/dev/null)
if [ "$ENV_PERMS" != "600" ] && [ "$ENV_PERMS" != "400" ]; then
    echo -e "${YELLOW}⚠️  WARNING: .env has permissive permissions ($ENV_PERMS)${NC}"
    echo "   Recommended: chmod 600 .env"
    ((WARNINGS++))
else
    echo -e "${GREEN}✅ .env has secure permissions${NC}"
fi

echo ""
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo -e "Errors:   ${RED}${ERRORS}${NC}"
echo -e "Warnings: ${YELLOW}${WARNINGS}${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ Validation FAILED with ${ERRORS} error(s)${NC}"
    echo "Please fix the errors above before deploying."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Validation PASSED with ${WARNINGS} warning(s)${NC}"
    echo "Consider addressing the warnings, especially for production."
    exit 0
else
    echo -e "${GREEN}✅ All checks PASSED!${NC}"
    echo "Environment is properly configured."
    exit 0
fi
