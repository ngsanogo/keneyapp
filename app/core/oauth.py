"""
OAuth2/OIDC authentication support for KeneyApp.
Enables integration with third-party identity providers.
"""

from typing import Any, Dict, Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status
from starlette.config import Config

from app.core.config import settings

# OAuth configuration
config = Config(".env")
oauth = OAuth(config)

# Register OAuth providers
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="microsoft",
    server_metadata_url="https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="okta",
    server_metadata_url=None,  # Will be configured via environment
    client_kwargs={"scope": "openid email profile"},
)


def verify_oidc_token(token: str, provider: str = "google") -> Optional[Dict[str, Any]]:
    """
    Verify and decode an OIDC token from a provider.

    Args:
        token: The OIDC token to verify
        provider: The OAuth provider name (google, microsoft, okta)

    Returns:
        Decoded token claims if valid, None otherwise
    """
    try:
        # Get the OAuth client for the provider
        client = oauth.create_client(provider)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' not configured",
            )

        # Verify token and get user info
        token_data = client.parse_id_token(token)

        return {
            "sub": token_data.get("sub"),
            "email": token_data.get("email"),
            "name": token_data.get("name"),
            "provider": provider,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid OIDC token: {str(e)}",
        )


async def get_oauth_authorization_url(
    provider: str, redirect_uri: str
) -> Dict[str, str]:
    """
    Generate authorization URL for OAuth flow.

    Args:
        provider: OAuth provider name
        redirect_uri: Redirect URI after authentication

    Returns:
        Dictionary with authorization_url and state
    """
    try:
        client = oauth.create_client(provider)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' not configured",
            )

        redirect_uri = (
            redirect_uri or f"{settings.APP_URL}/auth/oauth/callback/{provider}"
        )

        authorization_url, state = await client.create_authorization_url(
            redirect_uri=redirect_uri
        )

        return {"authorization_url": authorization_url, "state": state}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}",
        )


async def handle_oauth_callback(provider: str, code: str, state: str) -> Dict[str, Any]:
    """
    Handle OAuth callback and exchange code for token.

    Args:
        provider: OAuth provider name
        code: Authorization code from provider
        state: State parameter for CSRF protection

    Returns:
        User information from the provider
    """
    try:
        client = oauth.create_client(provider)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' not configured",
            )

        # Exchange code for token
        token = await client.authorize_access_token()

        # Parse ID token and get user info
        user_info = token.get("userinfo")
        if not user_info:
            user_info = await client.userinfo(token=token)

        return {
            "sub": user_info.get("sub"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "provider": provider,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OAuth callback failed: {str(e)}",
        )


__all__ = [
    "oauth",
    "verify_oidc_token",
    "get_oauth_authorization_url",
    "handle_oauth_callback",
]
