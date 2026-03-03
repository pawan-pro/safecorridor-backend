from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.RoutePatternResponse])
def get_routes(
    origin_region: str = Query(..., description="E.g., UAE, Saudi Arabia"),
    destination_region: str = Query(..., description="E.g., India-South, US-East"),
    db: Session = Depends(get_db)
):
    query = db.query(models.RoutePattern).filter(
        models.RoutePattern.origin_region == origin_region,
        models.RoutePattern.destination_region == destination_region
    )
    routes = query.all()
    
    # Enrich routes with airport data and evaluate overall status based on airports
    # Note: A real implementation would query all via_airports and calculate this
    route_responses = []
    for r in routes:
        # Fetch airport details for via_airports
        via_airports_data = db.query(models.Airport).filter(
            models.Airport.icao.in_(r.via_airports_icao)
        ).all()
        
        overall_status = r.status
        # Example logic: if any via airport is closed, mark overall UNAVAILABLE
        if any(a.status == models.StatusEnum.CLOSED for a in via_airports_data):
            overall_status = models.RouteStatusEnum.UNAVAILABLE
            
        r_dict = {
            "id": r.id,
            "origin_region": r.origin_region,
            "origin_airport_icao": r.origin_airport_icao,
            "destination_region": r.destination_region,
            "destination_airport_icao": r.destination_airport_icao,
            "via_airports_icao": r.via_airports_icao,
            "status": r.status,
            "reason": r.reason,
            "last_updated": r.last_updated,
            "overall_status": overall_status,
            "via_airports": via_airports_data
        }
        route_responses.append(schemas.RoutePatternResponse(**r_dict))
    
    return route_responses
