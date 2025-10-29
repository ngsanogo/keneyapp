"""
Prescription management router for digital prescription handling.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.prescription import Prescription
from app.schemas.prescription import PrescriptionCreate, PrescriptionResponse

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@router.post("/", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_prescription(prescription_data: PrescriptionCreate, db: Session = Depends(get_db)):
    """
    Create a new prescription.
    
    Args:
        prescription_data: Prescription information
        db: Database session
        
    Returns:
        Created prescription
    """
    db_prescription = Prescription(**prescription_data.model_dump())
    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)
    
    return db_prescription


@router.get("/", response_model=List[PrescriptionResponse])
def get_prescriptions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of prescriptions with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of prescriptions
    """
    prescriptions = db.query(Prescription).offset(skip).limit(limit).all()
    return prescriptions


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
def get_prescription(prescription_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific prescription by ID.
    
    Args:
        prescription_id: Prescription ID
        db: Database session
        
    Returns:
        Prescription record
    """
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found"
        )
    return prescription


@router.get("/patient/{patient_id}", response_model=List[PrescriptionResponse])
def get_patient_prescriptions(patient_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all prescriptions for a specific patient.
    
    Args:
        patient_id: Patient ID
        db: Database session
        
    Returns:
        List of patient's prescriptions
    """
    prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient_id).all()
    return prescriptions


@router.delete("/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prescription(prescription_id: int, db: Session = Depends(get_db)):
    """
    Delete a prescription.
    
    Args:
        prescription_id: Prescription ID
        db: Database session
    """
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found"
        )
    
    db.delete(prescription)
    db.commit()
