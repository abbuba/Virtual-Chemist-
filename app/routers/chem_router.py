from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.models import User
from app.schemas.molecule import MoleculeRequest
from app.services.chem_service import ChemicalService

router = APIRouter(prefix="/api/chemist", tags=["Virtual Chemist"])

@router.post("/combine")
def combine_atoms(
    payload: MoleculeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ChemicalService.evaluate_combination(db, payload.atoms, user)

@router.get("/profile")
def get_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ChemicalService.get_profile(db, user)

@router.get("/search")
def search(q: str = Query(..., min_length=2, max_length=200), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ChemicalService.search(db, q, user)

@router.get("/hint")
def hint(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ChemicalService.hint(db, user)
