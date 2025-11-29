"""
INS (Identifiant National de Santé) Service
Handles INS validation, verification, and teleservice integration
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.audit import log_audit_event
from app.exceptions import ValidationError
from app.models.french_healthcare import INSStatus, PatientINS


class INSService:
    """
    Service for managing French INS (Identifiant National de Santé)
    
    Implements ANS (Agence du Numérique en Santé) specifications:
    - INS format validation (13 digits + 2 key)
    - Luhn algorithm verification
    - Teleservice INS integration (API-based verification)
    - Identity trait matching
    """
    
    # INS format: 1 YY MM RR DDD KKK CC
    # 1: Gender (1=M, 2=F)
    # YY: Year of birth (2 digits)
    # MM: Month of birth
    # RR: Department or country code
    # DDD: Municipality code
    # KKK: Birth order in municipality
    # CC: Control key
    INS_PATTERN = re.compile(r'^[12]\d{12}$')
    
    def __init__(self, db: Session):
        self.db = db
        self.ins_api_url = settings.INS_API_URL if hasattr(settings, 'INS_API_URL') else None
        self.ins_api_key = settings.INS_API_KEY if hasattr(settings, 'INS_API_KEY') else None
    
    def validate_ins_format(self, ins_number: str) -> bool:
        """
        Validate INS number format (13 digits)
        
        Args:
            ins_number: INS number string
            
        Returns:
            True if format is valid
        """
        if not ins_number:
            return False
        
        # Remove spaces and hyphens
        clean_ins = ins_number.replace(" ", "").replace("-", "")
        
        # Check pattern
        return bool(self.INS_PATTERN.match(clean_ins))
    
    def calculate_ins_key(self, ins_number: str) -> str:
        """
        Calculate INS control key using Luhn algorithm (modified for INS)
        
        Args:
            ins_number: 13-digit INS number
            
        Returns:
            2-digit control key
        """
        if len(ins_number) != 13:
            raise ValidationError("INS must be exactly 13 digits")
        
        # Convert to integer for calculation
        try:
            ins_int = int(ins_number)
        except ValueError:
            raise ValidationError("INS must contain only digits")
        
        # Calculate key: 97 - (INS modulo 97)
        key = 97 - (ins_int % 97)
        return f"{key:02d}"
    
    def verify_ins_key(self, ins_number: str, key: str) -> bool:
        """
        Verify INS control key
        
        Args:
            ins_number: 13-digit INS number
            key: 2-digit control key
            
        Returns:
            True if key is valid
        """
        calculated_key = self.calculate_ins_key(ins_number)
        return calculated_key == key
    
    def parse_ins_components(self, ins_number: str) -> Dict[str, str]:
        """
        Parse INS components
        
        Args:
            ins_number: 13-digit INS number
            
        Returns:
            Dictionary with INS components
        """
        if len(ins_number) != 13:
            raise ValidationError("INS must be exactly 13 digits")
        
        return {
            "gender": ins_number[0],  # 1=M, 2=F
            "birth_year": ins_number[1:3],
            "birth_month": ins_number[3:5],
            "department_or_country": ins_number[5:7],
            "municipality": ins_number[7:10],
            "birth_order": ins_number[10:13]
        }
    
    async def verify_ins_with_teleservice(
        self,
        ins_number: str,
        birth_name: str,
        first_names: str,
        birth_date: datetime,
        birth_location: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Verify INS with ANS Teleservice INS API
        
        Args:
            ins_number: 13-digit INS number
            birth_name: Patient's birth name (nom de naissance)
            first_names: Patient's first names (prénoms)
            birth_date: Patient's birth date
            birth_location: Patient's birth location (optional)
            
        Returns:
            Tuple of (verification_success, identity_traits_dict)
        """
        if not self.ins_api_url or not self.ins_api_key:
            raise ValidationError(
                "INS Teleservice not configured. Set INS_API_URL and INS_API_KEY in environment."
            )
        
        # Prepare request payload (following ANS API spec)
        payload = {
            "ins": ins_number,
            "nom_naissance": birth_name.upper(),
            "prenoms": first_names.upper(),
            "date_naissance": birth_date.strftime("%Y-%m-%d"),
        }
        
        if birth_location:
            payload["lieu_naissance"] = birth_location
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ins_api_url}/v1/verify",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.ins_api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return True, data.get("identity_traits")
                elif response.status_code == 404:
                    # INS not found or identity mismatch
                    return False, None
                else:
                    raise ValidationError(f"INS verification failed: {response.text}")
                    
        except httpx.TimeoutException:
            raise ValidationError("INS Teleservice timeout")
        except httpx.RequestError as e:
            raise ValidationError(f"INS Teleservice error: {str(e)}")
    
    def create_or_update_ins_record(
        self,
        patient_id: UUID,
        ins_number: str,
        tenant_id: UUID,
        operator_id: UUID,
        identity_traits: Optional[Dict] = None,
        status: INSStatus = INSStatus.PENDING,
        verification_method: Optional[str] = None
    ) -> PatientINS:
        """
        Create or update PatientINS record
        
        Args:
            patient_id: Patient UUID
            ins_number: 13-digit INS number
            tenant_id: Tenant UUID
            operator_id: User performing verification
            identity_traits: Identity data from teleservice
            status: INS verification status
            verification_method: How INS was verified
            
        Returns:
            PatientINS record
        """
        # Check if record exists
        ins_record = self.db.query(PatientINS).filter(
            PatientINS.patient_id == patient_id
        ).first()
        
        now = datetime.utcnow()
        
        if ins_record:
            # Update existing
            ins_record.ins_number = ins_number
            ins_record.status = status
            ins_record.verification_operator_id = operator_id
            ins_record.verification_method = verification_method or ins_record.verification_method
            ins_record.last_check_at = now
            
            if status == INSStatus.VERIFIED:
                ins_record.verified_at = now
                ins_record.expires_at = now + timedelta(days=365)  # 1 year validity
            
            if identity_traits:
                ins_record.birth_name = identity_traits.get("nom_naissance")
                ins_record.first_names = identity_traits.get("prenoms")
                ins_record.birth_date = identity_traits.get("date_naissance")
                ins_record.birth_location = identity_traits.get("lieu_naissance")
                ins_record.birth_location_code = identity_traits.get("code_insee")
                ins_record.gender_code = identity_traits.get("sexe")
        else:
            # Create new
            ins_record = PatientINS(
                patient_id=patient_id,
                ins_number=ins_number,
                status=status,
                verification_operator_id=operator_id,
                verification_method=verification_method,
                tenant_id=tenant_id,
                last_check_at=now
            )
            
            if status == INSStatus.VERIFIED:
                ins_record.verified_at = now
                ins_record.expires_at = now + timedelta(days=365)
            
            if identity_traits:
                ins_record.birth_name = identity_traits.get("nom_naissance")
                ins_record.first_names = identity_traits.get("prenoms")
                ins_record.birth_date = identity_traits.get("date_naissance")
                ins_record.birth_location = identity_traits.get("lieu_naissance")
                ins_record.birth_location_code = identity_traits.get("code_insee")
                ins_record.gender_code = identity_traits.get("sexe")
            
            self.db.add(ins_record)
        
        self.db.commit()
        self.db.refresh(ins_record)
        
        return ins_record
    
    def get_patient_ins(self, patient_id: UUID) -> Optional[PatientINS]:
        """
        Get patient's INS record
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            PatientINS record or None
        """
        return self.db.query(PatientINS).filter(
            PatientINS.patient_id == patient_id
        ).first()
    
    def check_ins_expiry(self, ins_record: PatientINS) -> bool:
        """
        Check if INS verification has expired
        
        Args:
            ins_record: PatientINS record
            
        Returns:
            True if expired or expiring soon (within 30 days)
        """
        if not ins_record.expires_at:
            return False
        
        days_until_expiry = (ins_record.expires_at - datetime.utcnow()).days
        return days_until_expiry <= 30
    
    async def verify_and_store_ins(
        self,
        patient_id: UUID,
        ins_number: str,
        birth_name: str,
        first_names: str,
        birth_date: datetime,
        tenant_id: UUID,
        operator_id: UUID,
        birth_location: Optional[str] = None,
        request=None
    ) -> Tuple[PatientINS, bool]:
        """
        Full INS verification workflow: validate format, verify with teleservice, store
        
        Args:
            patient_id: Patient UUID
            ins_number: 13-digit INS number
            birth_name: Patient's birth name
            first_names: Patient's first names
            birth_date: Patient's birth date
            tenant_id: Tenant UUID
            operator_id: User performing verification
            birth_location: Patient's birth location (optional)
            request: FastAPI request for audit logging
            
        Returns:
            Tuple of (PatientINS record, verification_success)
        """
        # Clean INS
        clean_ins = ins_number.replace(" ", "").replace("-", "")
        
        # Validate format
        if not self.validate_ins_format(clean_ins):
            raise ValidationError("Invalid INS format. Must be 13 digits starting with 1 or 2.")
        
        # Verify with teleservice if configured
        verification_success = False
        identity_traits = None
        verification_method = "manual"
        status = INSStatus.PENDING
        
        if self.ins_api_url and self.ins_api_key:
            try:
                verification_success, identity_traits = await self.verify_ins_with_teleservice(
                    clean_ins, birth_name, first_names, birth_date, birth_location
                )
                verification_method = "teleservice_ins"
                status = INSStatus.VERIFIED if verification_success else INSStatus.FAILED
            except ValidationError:
                # Teleservice failed, but we'll store as pending
                status = INSStatus.PENDING
                verification_method = "manual"
        
        # Store record
        ins_record = self.create_or_update_ins_record(
            patient_id=patient_id,
            ins_number=clean_ins,
            tenant_id=tenant_id,
            operator_id=operator_id,
            identity_traits=identity_traits,
            status=status,
            verification_method=verification_method
        )
        
        # Audit log
        if request:
            log_audit_event(
                db=self.db,
                request=request,
                action="ins_verification",
                resource_type="patient_ins",
                resource_id=str(ins_record.id),
                user_id=operator_id,
                tenant_id=tenant_id,
                details={
                    "patient_id": str(patient_id),
                    "status": status.value,
                    "verification_method": verification_method,
                    "success": verification_success
                }
            )
        
        return ins_record, verification_success
