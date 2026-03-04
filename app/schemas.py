from pydantic import BaseModel, UUID4, Field, HttpUrl
from typing import List, Optional, Any
from datetime import datetime
from .models import (
    StatusEnum,
    AirspaceStatusEnum,
    AirlineOperationsEnum,
    RouteStatusEnum,
    AdvisorySourceType,
)

class AirportBase(BaseModel):
    icao: str
    iata: Optional[str] = None
    airport_name: Optional[str] = None
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_hub: bool = False
    display_status: StatusEnum = StatusEnum.UNKNOWN
    status: StatusEnum = StatusEnum.UNKNOWN
    airport_status: StatusEnum = StatusEnum.UNKNOWN
    airspace_status: AirspaceStatusEnum = AirspaceStatusEnum.UNKNOWN
    airline_operations: AirlineOperationsEnum = AirlineOperationsEnum.UNKNOWN
    status_reason: Optional[str] = None
    status_source: Optional[str] = None
    status_source_url: Optional[str] = None
    status_source_name: Optional[str] = None
    status_last_updated: Optional[datetime] = None
    last_verified_utc: Optional[datetime] = None

class AirportResponse(AirportBase):
    id: UUID4

    model_config = {"from_attributes": True}

class RoutePatternBase(BaseModel):
    origin_region: str
    origin_airport_icao: Optional[str] = None
    destination_region: str
    destination_airport_icao: Optional[str] = None
    via_airports_icao: List[str] = Field(default_factory=list)
    status: RouteStatusEnum = RouteStatusEnum.UNAVAILABLE
    reason: Optional[str] = None
    last_updated: Optional[datetime] = None

class RoutePatternResponse(RoutePatternBase):
    id: UUID4
    overall_status: Optional[RouteStatusEnum] = None
    via_airports: Optional[List[AirportResponse]] = None

    model_config = {"from_attributes": True}

class AdvisoryBase(BaseModel):
    source_type: AdvisorySourceType
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    airports_icao: List[str] = Field(default_factory=list)
    fir_codes: List[str] = Field(default_factory=list)
    airlines: List[str] = Field(default_factory=list)

class AdvisoryCreate(AdvisoryBase):
    raw_payload: Optional[Any] = None

class AdvisoryResponse(AdvisoryBase):
    id: UUID4
    created_at: datetime
    raw_payload: Optional[Any] = None

    model_config = {"from_attributes": True}


class OfficialUpdateCard(BaseModel):
    source_name: str
    source_type: str
    title: str
    summary: str
    url: Optional[str] = None
    published_at_utc: Optional[datetime] = None


class OfficialUpdateSnapshotResponse(BaseModel):
    id: UUID4
    summary: str
    last_updated_utc: Optional[datetime] = None
    cards: List[OfficialUpdateCard] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}
