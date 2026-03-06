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


class FlightStatusEntry(BaseModel):
    provider: str
    status: str
    status_label: str
    flight_date: Optional[str] = None
    departure_airport_code: str
    departure_airport: Optional[str] = None
    departure_iata: Optional[str] = None
    departure_icao: Optional[str] = None
    departure_terminal: Optional[str] = None
    departure_gate: Optional[str] = None
    departure_delay_minutes: Optional[int] = None
    departure_scheduled_utc: Optional[datetime | str] = None
    departure_estimated_utc: Optional[datetime | str] = None
    departure_actual_utc: Optional[datetime | str] = None
    arrival_airport: Optional[str] = None
    arrival_iata: Optional[str] = None
    arrival_icao: Optional[str] = None
    arrival_terminal: Optional[str] = None
    arrival_gate: Optional[str] = None
    arrival_baggage: Optional[str] = None
    arrival_delay_minutes: Optional[int] = None
    arrival_scheduled_utc: Optional[datetime | str] = None
    arrival_estimated_utc: Optional[datetime | str] = None
    airline_name: Optional[str] = None
    airline_iata: Optional[str] = None
    airline_icao: Optional[str] = None
    flight_number: Optional[str] = None
    flight_iata: Optional[str] = None
    flight_icao: Optional[str] = None
    flight_codeshared: Optional[Any] = None
    aircraft_registration: Optional[str] = None
    aircraft_icao24: Optional[str] = None
    live_latitude: Optional[float] = None
    live_longitude: Optional[float] = None
    live_altitude: Optional[float] = None
    live_speed_horizontal: Optional[float] = None
    live_is_ground: Optional[bool] = None


class FlightStatusSnapshotResponse(BaseModel):
    source_name: str
    source_type: str
    generated_at_utc: datetime
    requested_airports: List[str] = Field(default_factory=list)
    total: int
    flights: List[FlightStatusEntry] = Field(default_factory=list)


class LiveAgentCapabilities(BaseModel):
    voice_input: bool = True
    voice_output: bool = True
    interruption_support: bool = True
    multimodal_vision_hint: bool = True
    supported_regions: List[str] = Field(default_factory=list)
    last_updated_utc: datetime


class LiveChatRequest(BaseModel):
    prompt: str
    context: Optional[str] = None


class LiveChatResponse(BaseModel):
    message: str
    used_fallback: bool = False
    timestamp_utc: datetime


class LiveRouteRequest(BaseModel):
    origin_region: str
    destination_region: str


class LiveRouteOption(BaseModel):
    status: RouteStatusEnum
    reason: str
    via_airports_icao: List[str] = Field(default_factory=list)
    risk_score: int = Field(ge=0, le=100)


class LiveRouteResponse(BaseModel):
    origin_region: str
    destination_region: str
    recommended: Optional[LiveRouteOption] = None
    alternatives: List[LiveRouteOption] = Field(default_factory=list)
    summary: str
    generated_at_utc: datetime


class SosRequest(BaseModel):
    current_location: Optional[str] = None
    issue_context: Optional[str] = None


class SosResponse(BaseModel):
    status: str
    summary: str
    emergency_checklist: List[str] = Field(default_factory=list)
    created_at_utc: datetime
