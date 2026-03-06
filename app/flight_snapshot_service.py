import logging
import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from . import models
from .integrations.aviationstack import DEFAULT_UAE_DEPARTURE_AIRPORTS, fetch_uae_departures
from .schemas import FlightStatusSnapshotResponse


logger = logging.getLogger(__name__)

DEFAULT_FLIGHT_REFRESH_AIRPORTS = tuple(
    code.strip().upper()
    for code in os.getenv("FLIGHT_SNAPSHOT_AIRPORTS", ",".join(DEFAULT_UAE_DEPARTURE_AIRPORTS)).split(",")
    if code.strip()
)
DEFAULT_FLIGHT_REFRESH_LIMIT = int(os.getenv("FLIGHT_SNAPSHOT_PER_AIRPORT_LIMIT", "50"))


def _sort_flights(flights: list[dict]) -> list[dict]:
    return sorted(
        flights,
        key=lambda item: (
            item.get("departure_estimated_utc") or item.get("departure_scheduled_utc") or "",
            item.get("flight_iata") or "",
        ),
    )


def get_latest_snapshot(
    db: Session,
    airport_codes: list[str],
    per_airport_limit: int,
    flight_status: str | None,
) -> models.FlightStatusSnapshot | None:
    query = (
        db.query(models.FlightStatusSnapshot)
        .filter(
            models.FlightStatusSnapshot.per_airport_limit == per_airport_limit,
            models.FlightStatusSnapshot.flight_status_filter == flight_status,
        )
        .order_by(models.FlightStatusSnapshot.generated_at_utc.desc())
    )
    for snapshot in query.limit(25).all():
        if (snapshot.requested_airports or []) == airport_codes:
            return snapshot
    return None


def serialize_snapshot(snapshot: models.FlightStatusSnapshot) -> FlightStatusSnapshotResponse:
    return FlightStatusSnapshotResponse(
        source_name=snapshot.source_name,
        source_type=snapshot.source_type,
        generated_at_utc=snapshot.generated_at_utc,
        requested_airports=snapshot.requested_airports or [],
        total=snapshot.total,
        flights=snapshot.flights or [],
    )


async def refresh_and_store_snapshot(
    db: Session,
    airport_codes: list[str] | None = None,
    *,
    per_airport_limit: int = DEFAULT_FLIGHT_REFRESH_LIMIT,
    flight_status: str | None = None,
) -> models.FlightStatusSnapshot:
    requested_airports = airport_codes or list(DEFAULT_FLIGHT_REFRESH_AIRPORTS)
    flights = await fetch_uae_departures(
        requested_airports,
        per_airport_limit=per_airport_limit,
        flight_status=flight_status,
    )
    flights = _sort_flights(flights)

    snapshot = models.FlightStatusSnapshot(
        source_name="Aviationstack",
        source_type="flight_status_api",
        generated_at_utc=datetime.now(timezone.utc),
        requested_airports=requested_airports,
        per_airport_limit=per_airport_limit,
        flight_status_filter=flight_status,
        total=len(flights),
        flights=flights,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    logger.info(
        "Stored flight snapshot for airports=%s status=%s total=%s",
        ",".join(requested_airports),
        flight_status or "all",
        snapshot.total,
    )
    return snapshot
