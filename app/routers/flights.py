from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..flight_snapshot_service import get_latest_snapshot, refresh_and_store_snapshot, serialize_snapshot
from ..integrations.aviationstack import (
    AviationstackError,
    DEFAULT_UAE_DEPARTURE_AIRPORTS,
)
from ..schemas import FlightStatusSnapshotResponse


router = APIRouter()


@router.get("/status", response_model=FlightStatusSnapshotResponse)
async def get_flight_status(
    airports: Optional[str] = Query(
        default=",".join(DEFAULT_UAE_DEPARTURE_AIRPORTS),
        description="Comma-separated UAE departure airport IATA codes, e.g. DXB,AUH,SHJ",
    ),
    per_airport_limit: int = Query(default=50, ge=1, le=50),
    flight_status: Optional[str] = Query(default=None),
    force_refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    airport_codes = [code.strip().upper() for code in (airports or "").split(",") if code.strip()]
    if not airport_codes:
        airport_codes = list(DEFAULT_UAE_DEPARTURE_AIRPORTS)

    snapshot = None if force_refresh else get_latest_snapshot(db, airport_codes, per_airport_limit, flight_status)
    if snapshot is not None:
        return serialize_snapshot(snapshot)

    try:
        snapshot = await refresh_and_store_snapshot(
            db,
            airport_codes,
            per_airport_limit=per_airport_limit,
            flight_status=flight_status,
        )
    except AviationstackError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to fetch flight status feed.") from exc

    return serialize_snapshot(snapshot)
