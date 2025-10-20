from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.prescription import Prescription
from app.schemas.prescription import Prescription as PrescriptionSchema, PrescriptionCreate, PrescriptionUpdate
from app.routers.users import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[PrescriptionSchema])
async def read_prescriptions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prescriptions = db.query(Prescription).offset(skip).limit(limit).all()
    return prescriptions

@router.post("/", response_model=PrescriptionSchema)
async def create_prescription(
    prescription: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_prescription = Prescription(**prescription.dict())
    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)
    return db_prescription

@router.get("/{prescription_id}", response_model=PrescriptionSchema)
async def read_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if prescription is None:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return prescription

@router.put("/{prescription_id}", response_model=PrescriptionSchema)
async def update_prescription(
    prescription_id: int,
    prescription_update: PrescriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if prescription is None:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    update_data = prescription_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prescription, field, value)
    
    db.commit()
    db.refresh(prescription)
    return prescription

@router.delete("/{prescription_id}")
async def delete_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if prescription is None:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    db.delete(prescription)
    db.commit()
    return {"message": "Prescription deleted successfully"}
