from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..seed import seed_airports, seed_route_patterns

router = APIRouter()

# Stub: In a real implementation this would use Security headers or OAuth2
def get_admin_user():
    return True

@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_database(
    db: Session = Depends(get_db),
    admin_user: bool = Depends(get_admin_user)
):
    """Seed the database with initial airports and route patterns. One-time operation."""
    try:
        seed_airports(db)
        seed_route_patterns(db)
        return {"status": "ok", "message": "Database seeded successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/advisories", response_model=schemas.AdvisoryResponse, status_code=status.HTTP_201_CREATED)
def create_advisory(
    advisory: schemas.AdvisoryCreate,
    db: Session = Depends(get_db),
    admin_user: bool = Depends(get_admin_user)
):
    # Create the advisory
    new_advisory = models.Advisory(**advisory.model_dump())
    db.add(new_advisory)
    db.commit()
    db.refresh(new_advisory)
    return new_advisory
