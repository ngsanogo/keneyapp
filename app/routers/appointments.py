"""
Appointment management router for scheduling and tracking appointments.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_appointment(
    appointment_data: AppointmentCreate, db: Session = Depends(get_db)
):
    """
    Create a new appointment.

    Args:
        appointment_data: Appointment information
        db: Database session

    Returns:
        Created appointment
    """
    db_appointment = Appointment(**appointment_data.model_dump())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    return db_appointment


@router.get("/", response_model=List[AppointmentResponse])
def get_appointments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of appointments with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of appointments
    """
    appointments = db.query(Appointment).offset(skip).limit(limit).all()
    return appointments


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific appointment by ID.

    Args:
        appointment_id: Appointment ID
        db: Database session

    Returns:
        Appointment record
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an appointment.

    Args:
        appointment_id: Appointment ID
        appointment_data: Updated appointment information
        db: Database session

    Returns:
        Updated appointment
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    # Update only provided fields
    update_data = appointment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)

    db.commit()
    db.refresh(appointment)

    return appointment


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """
    Delete an appointment.

    Args:
        appointment_id: Appointment ID
        db: Database session
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    db.delete(appointment)
    db.commit()
