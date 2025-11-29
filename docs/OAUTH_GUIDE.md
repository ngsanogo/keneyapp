# OAuth2/OIDC Authentication Guide

## Overview

KeneyApp supports OAuth2/OIDC authentication for seamless integration with third-party identity providers. This enables single sign-on (SSO) and reduces password management overhead.

## Supported Providers

- **Google** - Google Workspace and Gmail accounts
- **Microsoft** - Azure AD / Microsoft 365 accounts
- **Okta** - Enterprise identity management

## Configuration

### Environment Variables

Add the following to your `.env` file:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# Okta OAuth
OKTA_CLIENT_ID=your-okta-client-id
OKTA_CLIENT_SECRET=your-okta-client-secret
OKTA_DOMAIN=your-domain.okta.com

# Application URL
APP_URL=https://your-domain.com
```

### Provider Setup

#### Google

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `{APP_URL}/api/v1/oauth/callback/google`
6. Copy Client ID and Client Secret

#### Microsoft

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to Azure Active Directory > App registrations
3. Create new registration
4. Add redirect URI: `{APP_URL}/api/v1/oauth/callback/microsoft`
5. Generate client secret
6. Copy Application (client) ID and client secret

#### Okta

1. Go to [Okta Admin Console](https://admin.okta.com/)
2. Navigate to Applications > Create App Integration
3. Select OIDC - Web Application
4. Add redirect URI: `{APP_URL}/api/v1/oauth/callback/okta`
5. Copy Client ID and Client Secret

## API Endpoints

### Initiate OAuth Flow

```http
GET /api/v1/oauth/authorize/{provider}
```

**Parameters:**

- `provider` (path): OAuth provider (google, microsoft, okta)
- `redirect_uri` (query, optional): Custom redirect URI

**Response:**

```json
{
  "authorization_url": "https://provider.com/oauth/authorize?...",
  "state": "random-csrf-token"
}
```

### Handle OAuth Callback

```http
GET /api/v1/oauth/callback/{provider}?code={code}&state={state}
```

**Parameters:**

- `provider` (path): OAuth provider
- `code` (query): Authorization code from provider
- `state` (query): CSRF protection token

**Response:**

```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

## Usage Examples

### Frontend Integration

```typescript
// Initiate OAuth login
async function loginWithGoogle() {
  const response = await fetch('/api/v1/oauth/authorize/google');
  const { authorization_url } = await response.json();

  // Redirect user to authorization URL
  window.location.href = authorization_url;
}

// Handle callback (on redirect page)
async function handleOAuthCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');
  const provider = getProviderFromUrl(); // Extract from URL

  const response = await fetch(
    `/api/v1/oauth/callback/${provider}?code=${code}&state=${state}`
  );

  const { access_token } = await response.json();

  // Store token and redirect to dashboard
  localStorage.setItem('token', access_token);
  window.location.href = '/dashboard';
}
```

### Python Client

```python
import requests

# Initiate OAuth flow
response = requests.get('https://api.keneyapp.com/api/v1/oauth/authorize/google')
auth_data = response.json()

print(f"Visit: {auth_data['authorization_url']}")

# After user authorizes, exchange code for token
code = input("Enter authorization code: ")
state = auth_data['state']

token_response = requests.get(
    f'https://api.keneyapp.com/api/v1/oauth/callback/google',
    params={'code': code, 'state': state}
)

access_token = token_response.json()['access_token']
print(f"Access Token: {access_token}")
```

## User Registration Flow

When a user authenticates via OAuth for the first time:

1. System checks if user exists by email
2. If not exists, auto-creates user account with:
   - Email from OAuth provider
   - Username derived from email
   - Full name from OAuth provider
   - Default role: `RECEPTIONIST`
   - Auto-generated password (not used for OAuth login)
3. User is logged in with JWT token
4. Audit log entry created

## Security Considerations

### CSRF Protection

- OAuth state parameter provides CSRF protection
- State is validated on callback
- Prevents authorization code interception attacks

### Token Storage

- JWT tokens are issued after successful OAuth authentication
- Frontend should store tokens securely (localStorage or sessionStorage)
- Include token in Authorization header for API requests

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Rate Limiting

OAuth endpoints are rate-limited:

- Authorization: 10 requests/minute
- Callback: 10 requests/minute

### Audit Logging

All OAuth authentication events are logged:

- User registration via OAuth
- Successful OAuth logins
- Failed authentication attempts

## Troubleshooting

### Invalid Client Credentials

**Error**: `OAuth provider not configured`

**Solution**: Verify environment variables are set correctly

### Redirect URI Mismatch

**Error**: `redirect_uri_mismatch`

**Solution**:

1. Check that redirect URI in provider console matches `{APP_URL}/api/v1/oauth/callback/{provider}`
2. Ensure `APP_URL` in `.env` matches your actual domain

### Email Not Provided

**Error**: `Email not provided by OAuth provider`

**Solution**:

1. Ensure email scope is requested
2. Verify user granted email permission
3. Check provider configuration

## Best Practices

1. **Use HTTPS**: Always use HTTPS in production for OAuth redirects
2. **Validate State**: Don't skip state parameter validation
3. **Secure Secrets**: Never commit OAuth secrets to version control
4. **Rotate Secrets**: Regularly rotate OAuth client secrets
5. **Monitor Usage**: Track OAuth authentication in audit logs
6. **User Consent**: Clearly communicate what data is accessed via OAuth

## Compliance

OAuth integration maintains HIPAA/GDPR compliance:

- OAuth providers must be BAA-compliant for HIPAA
- Users can revoke OAuth access at any time
- All OAuth events are audit logged
- OAuth tokens have limited validity (30 minutes)

## Support

For OAuth integration issues, contact: <ngsanogo@prooton.me>
