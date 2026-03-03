from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db

router = APIRouter()

@router.get("/status", response_model=List[schemas.AirportResponse])
def get_airports_status(
    country: Optional[str] = None,
    status: Optional[models.StatusEnum] = None,
    is_hub: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Airport)
    if country:
        query = query.filter(models.Airport.country == country)
    if status is not None:
        query = query.filter(models.Airport.status == status)
    if is_hub is not None:
        query = query.filter(models.Airport.is_hub == is_hub)
    return query.all()
