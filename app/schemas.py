from pydantic import BaseModel, UUID4, Field, HttpUrl
from typing import List, Optional, Any
from datetime import datetime
from .models import StatusEnum, RouteStatusEnum, AdvisorySourceType

class AirportBase(BaseModel):
    icao: str
    iata: Optional[str] = None
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_hub: bool = False
    status: StatusEnum = StatusEnum.UNKNOWN
    status_reason: Optional[str] = None
    status_source: Optional[str] = None
    status_last_updated: Optional[datetime] = None

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
