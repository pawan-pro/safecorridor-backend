from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.AdvisoryResponse])
def get_advisories(
    airport_icao: Optional[str] = None,
    fir_code: Optional[str] = None,
    airline: Optional[str] = None,
    source_type: Optional[models.AdvisorySourceType] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(models.Advisory)
    
    # Filtering ARRAY columns in PostgreSQL requires specific operators.
    if airport_icao:
        query = query.filter(models.Advisory.airports_icao.contains([airport_icao]))
    if fir_code:
        query = query.filter(models.Advisory.fir_codes.contains([fir_code]))
    if airline:
        query = query.filter(models.Advisory.airlines.contains([airline]))
    if source_type:
        query = query.filter(models.Advisory.source_type == source_type)
        
    query = query.order_by(models.Advisory.created_at.desc())
    offset = (page - 1) * size
    return query.offset(offset).limit(size).all()
