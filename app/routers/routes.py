import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter()


def _airport_status_rank(status: models.StatusEnum) -> int:
    rank = {
        models.StatusEnum.OPEN: 0,
        models.StatusEnum.RESTRICTED: 1,
        models.StatusEnum.UNKNOWN: 2,
        models.StatusEnum.CLOSED: 3,
    }
    return rank.get(status, 3)


def _display_status_enum(airport: models.Airport) -> models.StatusEnum:
    try:
        return models.StatusEnum((airport.display_status or "UNKNOWN").upper())
    except Exception:
        return models.StatusEnum.UNKNOWN


def _derive_route_status(via_airports: List[models.Airport], default_status: models.RouteStatusEnum) -> models.RouteStatusEnum:
    if not via_airports:
        return default_status

    statuses = {_display_status_enum(a) for a in via_airports}
    if models.StatusEnum.CLOSED in statuses:
        return models.RouteStatusEnum.UNAVAILABLE
    if models.StatusEnum.UNKNOWN in statuses:
        return models.RouteStatusEnum.DISCOURAGED
    if models.StatusEnum.RESTRICTED in statuses:
        return models.RouteStatusEnum.DISCOURAGED
    return models.RouteStatusEnum.RECOMMENDED


def _build_route(
    origin_region: str,
    destination_region: str,
    via_icaos: List[str],
    reason: str,
    db: Session,
    default_status: models.RouteStatusEnum = models.RouteStatusEnum.RECOMMENDED,
) -> schemas.RoutePatternResponse:
    via_airports = []
    if via_icaos:
        via_airports = (
            db.query(models.Airport)
            .filter(models.Airport.icao.in_(via_icaos))
            .all()
        )
        via_airports = sorted(via_airports, key=lambda a: _airport_status_rank(_display_status_enum(a)))

    overall_status = _derive_route_status(via_airports, default_status)
    base_status = default_status if default_status == models.RouteStatusEnum.UNAVAILABLE else overall_status

    return schemas.RoutePatternResponse(
        id=uuid.uuid4(),
        origin_region=origin_region,
        destination_region=destination_region,
        via_airports_icao=[a.icao for a in via_airports],
        status=base_status,
        overall_status=overall_status,
        reason=reason,
        last_updated=datetime.now(timezone.utc),
        via_airports=via_airports,
    )


@router.get("/", response_model=List[schemas.RoutePatternResponse])
@router.get("", response_model=List[schemas.RoutePatternResponse], include_in_schema=False)
def get_routes(
    origin_region: str = Query(..., description="E.g., UAE, Saudi Arabia"),
    destination_region: str = Query(..., description="E.g., India-South, US-East"),
    db: Session = Depends(get_db),
):
    airports = {a.icao: a for a in db.query(models.Airport).all()}

    def has_operational(*icaos: str):
        return [
            icao
            for icao in icaos
            if icao in airports and _display_status_enum(airports[icao]) in {models.StatusEnum.OPEN, models.StatusEnum.RESTRICTED}
        ]

    routes: List[schemas.RoutePatternResponse] = []

    # UAE / GCC to India corridors
    if destination_region in {"India-South", "India-West", "India-All"}:
        if origin_region in {"UAE", "UAE-Road", "Gulf-Other", "Gulf-All"}:
            oman_corridor = has_operational("OOMS")
            if oman_corridor:
                routes.append(
                    _build_route(
                        origin_region,
                        destination_region,
                        oman_corridor,
                        "UAE/GCC to India corridor via Muscat remains the most plausible path during ongoing Gulf disruptions.",
                        db,
                        models.RouteStatusEnum.RECOMMENDED,
                    )
                )

            saudi_corridor = has_operational("OERK", "OEJN", "OEDF")
            if saudi_corridor:
                routes.append(
                    _build_route(
                        origin_region,
                        destination_region,
                        [saudi_corridor[0]],
                        "Saudi hubs are currently operational and may offer alternate onward connectivity to India.",
                        db,
                        models.RouteStatusEnum.DISCOURAGED,
                    )
                )

            if origin_region == "UAE":
                direct_uae = has_operational("OMDB", "OMAA", "OMDW", "OMSJ")
                if direct_uae:
                    routes.append(
                        _build_route(
                            origin_region,
                            destination_region,
                            [direct_uae[0]],
                            "Limited UAE departures may operate under strict control measures; confirm directly with airlines.",
                            db,
                            models.RouteStatusEnum.DISCOURAGED,
                        )
                    )
                else:
                    routes.append(
                        _build_route(
                            origin_region,
                            destination_region,
                            [],
                            "Direct UAE commercial corridor is currently unavailable due to severe restrictions at UAE hubs.",
                            db,
                            models.RouteStatusEnum.UNAVAILABLE,
                        )
                    )

    # Gulf/India to US corridors via Europe
    if destination_region in {"US-East", "US-West"} and origin_region in {"Gulf-All", "India-All", "Europe-West"}:
        europe_corridor = has_operational("LIRF", "EDDM")
        if europe_corridor:
            routes.append(
                _build_route(
                    origin_region,
                    destination_region,
                    europe_corridor[:2],
                    "Europe hubs remain viable technical and transfer points for long-haul routings while Gulf airspace remains constrained.",
                    db,
                    models.RouteStatusEnum.RECOMMENDED if destination_region == "US-East" else models.RouteStatusEnum.DISCOURAGED,
                )
            )

    # Europe to India direct corridor
    if origin_region == "Europe-West" and destination_region in {"India-All", "India-South", "India-West"}:
        routes.append(
            _build_route(
                origin_region,
                destination_region,
                [],
                "Europe-to-India services are broadly operational with schedule variability; verify latest carrier advisories.",
                db,
                models.RouteStatusEnum.RECOMMENDED,
            )
        )

    # Fallback to stored static patterns if no generated route
    if not routes:
        static_routes = db.query(models.RoutePattern).filter(
            models.RoutePattern.origin_region == origin_region,
            models.RoutePattern.destination_region == destination_region,
        ).all()
        for route in static_routes:
            routes.append(
                _build_route(
                    route.origin_region,
                    route.destination_region,
                    route.via_airports_icao or [],
                    route.reason or "Stored fallback route pattern.",
                    db,
                    route.status,
                )
            )

    return routes
