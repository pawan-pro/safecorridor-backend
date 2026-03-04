import uuid
from sqlalchemy import Column, String, Boolean, Enum, Text, DateTime, JSON
from .database import Base
from datetime import datetime, timezone
import enum

class StatusEnum(str, enum.Enum):
    OPEN = "OPEN"
    RESTRICTED = "RESTRICTED"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


class AirspaceStatusEnum(str, enum.Enum):
    OPEN = "OPEN"
    RESTRICTED = "RESTRICTED"
    PARTIAL = "PARTIAL"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


class AirlineOperationsEnum(str, enum.Enum):
    NORMAL = "NORMAL"
    LIMITED = "LIMITED"
    SUSPENDED = "SUSPENDED"
    EVACUATION_ONLY = "EVACUATION_ONLY"
    UNKNOWN = "UNKNOWN"

class RouteStatusEnum(str, enum.Enum):
    RECOMMENDED = "RECOMMENDED"
    DISCOURAGED = "DISCOURAGED"
    UNAVAILABLE = "UNAVAILABLE"

class AdvisorySourceType(str, enum.Enum):
    NOTAM = "NOTAM"
    AIRLINE = "AIRLINE"
    AIRPORT = "AIRPORT"
    GOVERNMENT = "GOVERNMENT"
    MEDIA = "MEDIA"

class Airport(Base):
    __tablename__ = "airports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    icao = Column(String, unique=True, index=True, nullable=False)
    iata = Column(String, index=True)
    name = Column(String)
    city = Column(String)
    country = Column(String)
    is_hub = Column(Boolean, default=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.UNKNOWN)
    airport_status = Column(String, default=StatusEnum.UNKNOWN.value, nullable=False)
    airspace_status = Column(String, default=AirspaceStatusEnum.UNKNOWN.value, nullable=False)
    airline_operations = Column(String, default=AirlineOperationsEnum.UNKNOWN.value, nullable=False)
    status_reason = Column(Text)
    status_source = Column(String)
    status_source_name = Column(String)
    status_last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_verified_utc = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def display_status(self) -> str:
        value = (self.airport_status or "").upper()
        if value in {StatusEnum.CLOSED.value, StatusEnum.RESTRICTED.value, StatusEnum.OPEN.value}:
            return value
        if self.status:
            try:
                return self.status.value
            except Exception:
                pass
        return StatusEnum.UNKNOWN.value

    @property
    def status_source_url(self) -> str | None:
        return self.status_source

    @property
    def airport_name(self) -> str | None:
        return self.name

class AirspaceRegion(Base):
    __tablename__ = "airspace_regions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    status = Column(Enum(StatusEnum), default=StatusEnum.UNKNOWN)
    status_reason = Column(Text)
    status_source = Column(String)
    status_last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class RoutePattern(Base):
    __tablename__ = "route_patterns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    origin_region = Column(String, index=True)
    origin_airport_icao = Column(String, nullable=True)
    destination_region = Column(String, index=True)
    destination_airport_icao = Column(String, nullable=True)
    via_airports_icao = Column(JSON, default=list)
    status = Column(Enum(RouteStatusEnum), default=RouteStatusEnum.UNAVAILABLE)
    reason = Column(Text)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Advisory(Base):
    __tablename__ = "advisories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_type = Column(Enum(AdvisorySourceType), nullable=False)
    source_name = Column(String)
    source_url = Column(String)
    title = Column(String)
    summary = Column(Text)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    airports_icao = Column(JSON, default=list)
    fir_codes = Column(JSON, default=list)
    airlines = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    raw_payload = Column(JSON, nullable=True)


class OfficialUpdateSnapshot(Base):
    __tablename__ = "official_update_snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    summary = Column(Text, nullable=False)
    last_updated_utc = Column(DateTime(timezone=True), nullable=True)
    cards = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
