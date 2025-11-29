"""
Pro Santé Connect (PSC) OAuth2/OIDC Integration
French healthcare professional authentication system
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID

import httpx
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.exceptions import AuthenticationError, ValidationError
from app.models.french_healthcare import CPSType, HealthcareProfessionalCPS
from app.models.user import User, UserRole


class ProSanteConnectService:
    """
    Pro Santé Connect (PSC) integration service
    
    Implements OAuth2/OIDC flow for French healthcare professional authentication
    using CPS/e-CPS credentials.
    
    Documentation: https://industriels.esante.gouv.fr/produits-services/pro-sante-connect
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.client_id = settings.PSC_CLIENT_ID
        self.client_secret = settings.PSC_CLIENT_SECRET
        self.authorization_endpoint = settings.PSC_AUTHORIZATION_ENDPOINT
        self.token_endpoint = settings.PSC_TOKEN_ENDPOINT
        self.userinfo_endpoint = settings.PSC_USERINFO_ENDPOINT
        self.jwks_uri = settings.PSC_JWKS_URI
        self.scope = settings.PSC_SCOPE
        self.redirect_uri = f"{settings.APP_URL}/api/v1/auth/psc/callback"
    
    def get_authorization_url(self, state: str) -> str:
        """
        Generate PSC authorization URL for OAuth2 flow
        
        Args:
            state: Random state parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        if not self.client_id:
            raise ValidationError("Pro Santé Connect not configured. Set PSC_CLIENT_ID.")
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": state,
            "nonce": state,  # Use same value for simplicity
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorization_endpoint}?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from PSC callback
            
        Returns:
            Token response dict with access_token, id_token, etc.
        """
        if not self.client_id or not self.client_secret:
            raise ValidationError("Pro Santé Connect credentials not configured.")
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    raise AuthenticationError(f"PSC token exchange failed: {response.text}")
                
                return response.json()
                
        except httpx.RequestError as e:
            raise AuthenticationError(f"PSC token exchange error: {str(e)}")
    
    async def get_user_info(self, access_token: str) -> Dict:
        """
        Retrieve user information from PSC userinfo endpoint
        
        Args:
            access_token: Access token from PSC
            
        Returns:
            User info dict with RPPS, specialty, etc.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    raise AuthenticationError(f"PSC userinfo failed: {response.text}")
                
                return response.json()
                
        except httpx.RequestError as e:
            raise AuthenticationError(f"PSC userinfo error: {str(e)}")
    
    def decode_id_token(self, id_token: str) -> Dict:
        """
        Decode and validate PSC ID token (JWT)
        
        Args:
            id_token: JWT ID token from PSC
            
        Returns:
            Decoded token claims
        """
        try:
            # In production, fetch and cache JWKS from PSC_JWKS_URI
            # For now, we'll decode without verification (NOT for production)
            # TODO: Implement proper JWKS verification
            decoded = jwt.decode(
                id_token,
                options={"verify_signature": False}  # FIXME: Verify in production!
            )
            return decoded
        except JWTError as e:
            raise AuthenticationError(f"Invalid PSC ID token: {str(e)}")
    
    async def authenticate_with_psc(
        self,
        code: str,
        tenant_id: UUID
    ) -> tuple[User, HealthcareProfessionalCPS, str]:
        """
        Complete PSC authentication flow
        
        Args:
            code: Authorization code from PSC callback
            tenant_id: Tenant UUID
            
        Returns:
            Tuple of (User, HealthcareProfessionalCPS, access_token)
        """
        # Exchange code for tokens
        token_response = await self.exchange_code_for_token(code)
        access_token = token_response["access_token"]
        id_token = token_response.get("id_token")
        
        # Get user info
        user_info = await self.get_user_info(access_token)
        
        # Decode ID token for additional claims
        id_claims = self.decode_id_token(id_token) if id_token else {}
        
        # Extract healthcare professional details
        rpps_number = user_info.get("rpps") or id_claims.get("rpps")
        given_name = user_info.get("given_name", "")
        family_name = user_info.get("family_name", "")
        email = user_info.get("email")
        sub = user_info.get("sub")  # PSC subject identifier
        
        if not rpps_number:
            raise AuthenticationError("No RPPS number found in PSC response")
        
        # Check if CPS record exists
        cps_record = self.db.query(HealthcareProfessionalCPS).filter(
            HealthcareProfessionalCPS.rpps_number == rpps_number,
            HealthcareProfessionalCPS.tenant_id == tenant_id
        ).first()
        
        if cps_record:
            # Update existing CPS record
            user = cps_record.user
            cps_record.psc_sub = sub
            cps_record.psc_last_login = datetime.utcnow()
            
            # Update user info if changed
            if email and not user.email:
                user.email = email
            if given_name or family_name:
                user.full_name = f"{given_name} {family_name}".strip()
        else:
            # Create new user and CPS record
            username = f"psc_{rpps_number}"
            
            # Check if user exists by email or username
            existing_user = None
            if email:
                existing_user = self.db.query(User).filter(
                    User.email == email,
                    User.tenant_id == tenant_id
                ).first()
            
            if not existing_user:
                existing_user = self.db.query(User).filter(
                    User.username == username,
                    User.tenant_id == tenant_id
                ).first()
            
            if existing_user:
                user = existing_user
            else:
                # Create new user
                user = User(
                    username=username,
                    email=email or f"{rpps_number}@psc.local",
                    full_name=f"{given_name} {family_name}".strip() or f"Dr. {rpps_number}",
                    role=UserRole.DOCTOR,  # Default role for PSC users
                    is_active=True,
                    tenant_id=tenant_id,
                    hashed_password="",  # No password for PSC users
                )
                self.db.add(user)
                self.db.flush()
            
            # Create CPS record
            cps_record = HealthcareProfessionalCPS(
                user_id=user.id,
                cps_type=CPSType.E_CPS,
                cps_number="",  # Will be updated when available
                rpps_number=rpps_number,
                profession_code=user_info.get("profession_code"),
                profession_category=user_info.get("profession_category"),
                specialty_code=user_info.get("specialty_code"),
                specialty_label=user_info.get("specialty_label"),
                psc_sub=sub,
                psc_last_login=datetime.utcnow(),
                is_active=True,
                tenant_id=tenant_id
            )
            self.db.add(cps_record)
        
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(cps_record)
        
        # Generate KeneyApp access token
        keneyapp_token = create_access_token(
            data={
                "sub": user.username,
                "user_id": str(user.id),
                "tenant_id": str(tenant_id),
                "role": user.role.value,
                "psc_authenticated": True,
                "rpps": rpps_number
            }
        )
        
        return user, cps_record, keneyapp_token
    
    def get_cps_by_user_id(self, user_id: UUID) -> Optional[HealthcareProfessionalCPS]:
        """
        Get CPS record by user ID
        
        Args:
            user_id: User UUID
            
        Returns:
            HealthcareProfessionalCPS record or None
        """
        return self.db.query(HealthcareProfessionalCPS).filter(
            HealthcareProfessionalCPS.user_id == user_id
        ).first()
    
    def verify_cps_validity(self, cps_record: HealthcareProfessionalCPS) -> bool:
        """
        Verify if CPS credential is still valid
        
        Args:
            cps_record: HealthcareProfessionalCPS record
            
        Returns:
            True if valid
        """
        return cps_record.is_valid
