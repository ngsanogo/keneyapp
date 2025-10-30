"""
GraphQL Schema for KeneyApp.
Provides GraphQL API alongside REST for complex queries.
"""

from typing import List, Optional
import strawberry
from strawberry.fastapi import GraphQLRouter
from datetime import datetime

from app.models.user import UserRole


@strawberry.type
class UserType:
    """GraphQL User type."""
    id: int
    email: str
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


@strawberry.type
class PatientType:
    """GraphQL Patient type."""
    id: int
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    medical_history: Optional[str]
    allergies: Optional[str]
    blood_type: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    created_at: datetime


@strawberry.type
class AppointmentType:
    """GraphQL Appointment type."""
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    reason: Optional[str]
    status: str
    notes: Optional[str]
    created_at: datetime


@strawberry.type
class PrescriptionType:
    """GraphQL Prescription type."""
    id: int
    patient_id: int
    doctor_id: int
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str]
    refills: int
    prescribed_date: datetime
    created_at: datetime


@strawberry.type
class Query:
    """GraphQL Query root."""
    
    @strawberry.field
    def hello(self) -> str:
        """Simple hello query for testing."""
        return "Hello from KeneyApp GraphQL API!"
    
    @strawberry.field
    def api_version(self) -> str:
        """Get API version."""
        return "1.0.0"


@strawberry.type
class Mutation:
    """GraphQL Mutation root."""
    
    @strawberry.mutation
    def placeholder(self) -> bool:
        """Placeholder mutation."""
        return True


# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)


def create_graphql_router() -> GraphQLRouter:
    """
    Create and configure GraphQL router.
    
    Returns:
        Configured GraphQL router
    """
    return GraphQLRouter(schema)


__all__ = [
    'schema',
    'create_graphql_router',
    'UserType',
    'PatientType',
    'AppointmentType',
    'PrescriptionType',
]
