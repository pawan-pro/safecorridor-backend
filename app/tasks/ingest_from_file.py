import json
import logging
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx

# Add the parent directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal
from app import models
from app.db_migrations import ensure_airport_columns

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ICAO_METADATA = {
    "OMDB": {"iata": "DXB", "name": "Dubai International Airport", "city": "Dubai", "country": "United Arab Emirates"},
    "OMDW": {"iata": "DWC", "name": "Al Maktoum International Airport", "city": "Dubai", "country": "United Arab Emirates"},
    "OMAA": {"iata": "AUH", "name": "Zayed International Airport", "city": "Abu Dhabi", "country": "United Arab Emirates"},
    "OMSJ": {"iata": "SHJ", "name": "Sharjah International Airport", "city": "Sharjah", "country": "United Arab Emirates"},
    "OTHH": {"iata": "DOH", "name": "Hamad International Airport", "city": "Doha", "country": "Qatar"},
    "OBBI": {"iata": "BAH", "name": "Bahrain International Airport", "city": "Muharraq", "country": "Bahrain"},
    "OKBK": {"iata": "KWI", "name": "Kuwait International Airport", "city": "Kuwait City", "country": "Kuwait"},
    "OERK": {"iata": "RUH", "name": "King Khalid International Airport", "city": "Riyadh", "country": "Saudi Arabia"},
    "OEJN": {"iata": "JED", "name": "King Abdulaziz International Airport", "city": "Jeddah", "country": "Saudi Arabia"},
    "OEDF": {"iata": "DMM", "name": "King Fahd International Airport", "city": "Dammam", "country": "Saudi Arabia"},
    "OOMS": {"iata": "MCT", "name": "Muscat International Airport", "city": "Muscat", "country": "Oman"},
    "VIDP": {"iata": "DEL", "name": "Indira Gandhi International Airport", "city": "Delhi", "country": "India"},
    "VABB": {"iata": "BOM", "name": "Chhatrapati Shivaji Maharaj International Airport", "city": "Mumbai", "country": "India"},
    "LIRF": {"iata": "FCO", "name": "Leonardo da Vinci–Fiumicino Airport", "city": "Rome", "country": "Italy"},
    "EDDM": {"iata": "MUC", "name": "Munich International Airport", "city": "Munich", "country": "Germany"},
}

NEWS_DOMAINS = {
    "gulfnews.com",
    "khaleejtimes.com",
    "timesofindia.indiatimes.com",
    "economictimes.indiatimes.com",
    "dw.com",
    "sundayguardianlive.com",
    "visahq.com",
    "thehindu.com",
    "hindustantimes.com",
    "indianeagle.com",
    "travelandtourworld.com",
}

OFFICIAL_AIRPORT_DOMAINS = {
    "OMDB": {"dubaiairports.ae"},
    "OMDW": {"dubaiairports.ae"},
    "OMAA": {"abudhabiairports.ae"},
    "OMSJ": {"sharjahinternationalairport.com"},
    "OTHH": {"dohahamadairport.com", "hamadairport.com"},
    "OBBI": {"bahrainairport.bh"},
    "OKBK": {"kuwaitairport.gov.kw"},
    "OERK": {"kkia.sa", "riyadhairports.com"},
    "OEJN": {"gaca.gov.sa", "jeddah-airport.com"},
    "OEDF": {"dammamairports.com", "gaca.gov.sa"},
    "OOMS": {"omanairports.co.om"},
    "VIDP": {"newdelhiairport.in"},
    "VABB": {"csmia.adaniairports.com"},
    "LIRF": {"adr.it"},
    "EDDM": {"munich-airport.com"},
}

_redirect_cache: dict[str, str] = {}


def resolve_final_url(url: str | None) -> str | None:
    if not url:
        return None
    if url in _redirect_cache:
        return _redirect_cache[url]
    try:
        with httpx.Client(follow_redirects=True, timeout=6.0) as client:
            response = client.get(url)
            final_url = str(response.url)
            _redirect_cache[url] = final_url
            return final_url
    except Exception:
        _redirect_cache[url] = url
        return url


def _is_news_domain(url: str | None) -> bool:
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith(f".{d}") for d in NEWS_DOMAINS)


def _is_official_airport_domain(icao: str, url: str | None) -> bool:
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    allowed = OFFICIAL_AIRPORT_DOMAINS.get(icao, set())
    return any(host == d or host.endswith(f".{d}") for d in allowed)


def infer_source_fields(icao: str, source_url: str | None, source_name: str | None):
    normalized_name = (source_name or "").strip()
    source_type = models.AdvisorySourceType.AIRPORT
    final_url = resolve_final_url(source_url)

    if final_url and _is_news_domain(final_url):
        source_type = models.AdvisorySourceType.MEDIA
        normalized_name = "News"
    elif source_url and _is_news_domain(source_url):
        source_type = models.AdvisorySourceType.MEDIA
        normalized_name = "News"
    elif source_url and not _is_official_airport_domain(icao, source_url):
        # If source is neither official airport domain nor explicit authority domain,
        # treat it as media-style reference to reduce misleading "AIRPORT" labels.
        url_lower = source_url.lower()
        if any(token in url_lower for token in ["news", "article", "story", "report"]):
            source_type = models.AdvisorySourceType.MEDIA
            normalized_name = "News"

    if not normalized_name:
        normalized_name = "Perplexity JSON Ingest"

    return source_type, normalized_name


def ingest_airports_from_file(path: str = "data/perplexity_airports.json"):
    """
    Ingest airport status from an offline JSON file generated by Perplexity.
    """
    if not os.path.exists(path):
        logger.error(f"File not found: {path}")
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return

    airports_data = data.get("airports", [])
    official_updates = data.get("official_updates")
    if not airports_data:
        logger.warning(f"No 'airports' array found in {path}")
        return

    ensure_airport_columns()
    db = SessionLocal()
    try:
        logger.info(f"Starting ingestion of {len(airports_data)} airports from {path}...")
        
        status_map = {
            "OPEN": models.StatusEnum.OPEN,
            "RESTRICTED": models.StatusEnum.RESTRICTED,
            "CLOSED": models.StatusEnum.CLOSED,
            "UNKNOWN": models.StatusEnum.UNKNOWN,
        }
        airspace_status_allowed = {s.value for s in models.AirspaceStatusEnum}
        airline_ops_allowed = {s.value for s in models.AirlineOperationsEnum}

        def normalize_airport_status(item: dict) -> str:
            value = (item.get("airport_status") or item.get("status") or "UNKNOWN").upper()
            return value if value in status_map else models.StatusEnum.UNKNOWN.value

        def normalize_airspace_status(item: dict, airport_status_value: str) -> str:
            value = (item.get("airspace_status") or "").upper()
            if value in airspace_status_allowed:
                return value
            # Backward compatible inference when source only sends a single status
            if airport_status_value == models.StatusEnum.CLOSED.value:
                return models.AirspaceStatusEnum.CLOSED.value
            if airport_status_value == models.StatusEnum.RESTRICTED.value:
                return models.AirspaceStatusEnum.RESTRICTED.value
            if airport_status_value == models.StatusEnum.OPEN.value:
                return models.AirspaceStatusEnum.OPEN.value
            return models.AirspaceStatusEnum.UNKNOWN.value

        def normalize_airline_ops(item: dict, airport_status_value: str, airspace_status_value: str) -> str:
            value = (item.get("airline_operations") or "").upper()
            if value in airline_ops_allowed:
                return value
            # Inference rules for partial sources
            if airspace_status_value == models.AirspaceStatusEnum.CLOSED.value:
                return models.AirlineOperationsEnum.SUSPENDED.value
            if airspace_status_value in {models.AirspaceStatusEnum.RESTRICTED.value, models.AirspaceStatusEnum.PARTIAL.value}:
                return models.AirlineOperationsEnum.LIMITED.value
            if airport_status_value == models.StatusEnum.CLOSED.value:
                return models.AirlineOperationsEnum.SUSPENDED.value
            if airport_status_value == models.StatusEnum.RESTRICTED.value:
                return models.AirlineOperationsEnum.LIMITED.value
            if airport_status_value == models.StatusEnum.OPEN.value and airspace_status_value == models.AirspaceStatusEnum.OPEN.value:
                return models.AirlineOperationsEnum.NORMAL.value
            return models.AirlineOperationsEnum.UNKNOWN.value

        for item in airports_data:
            icao = item.get("icao")
            if not icao:
                continue

            airport = db.query(models.Airport).filter(models.Airport.icao == icao).first()
            if not airport:
                metadata = ICAO_METADATA.get(icao, {})
                airport = models.Airport(
                    icao=icao,
                    iata=metadata.get("iata"),
                    name=metadata.get("name", icao),
                    city=metadata.get("city"),
                    country=metadata.get("country", "Unknown"),
                    is_hub=True,
                )
                db.add(airport)
                logger.info(f"Airport {icao} not found in DB, created from ingestion metadata.")

            airport_status_value = normalize_airport_status(item)
            airspace_status_value = normalize_airspace_status(item, airport_status_value)
            airline_ops_value = normalize_airline_ops(item, airport_status_value, airspace_status_value)

            airport.status = status_map.get(airport_status_value, models.StatusEnum.UNKNOWN)
            airport.airport_status = airport_status_value
            airport.airspace_status = airspace_status_value
            airport.airline_operations = airline_ops_value
            airport.status_reason = item.get("status_reason")
            airport.status_source = item.get("status_source_url")
            airport.status_source_name = item.get("status_source_name")
            airport.status_last_updated = datetime.now(timezone.utc)
            last_verified_raw = item.get("last_verified_utc")
            if isinstance(last_verified_raw, str):
                try:
                    airport.last_verified_utc = datetime.fromisoformat(last_verified_raw.replace("Z", "+00:00"))
                except ValueError:
                    airport.last_verified_utc = datetime.now(timezone.utc)
            else:
                airport.last_verified_utc = datetime.now(timezone.utc)
            
            # Optional Advisory
            # Since the requirement says "Optionally create an Advisory", we'll create it.
            # Avoid duplicating identical advisories if run multiple times.
            airport_display = airport.name or icao
            advisory_title = f"Status update for {airport_display} ({icao})"
            source_url = item.get("status_source_url")
            summary = item.get("status_reason")
            source_type, source_name = infer_source_fields(icao, source_url, item.get("status_source_name"))
            
            existing_advisory = db.query(models.Advisory).filter(
                models.Advisory.title == advisory_title,
                models.Advisory.summary == summary
            ).first()
            
            if not existing_advisory:
                advisory = models.Advisory(
                    source_type=source_type,
                    source_name=source_name,
                    source_url=source_url,
                    title=advisory_title,
                    summary=summary,
                    airports_icao=[icao],
                    raw_payload={
                        "airport_status": airport_status_value,
                        "airspace_status": airspace_status_value,
                        "airline_operations": airline_ops_value,
                    },
                )
                db.add(advisory)
            else:
                existing_advisory.source_type = source_type
                existing_advisory.source_name = source_name
                existing_advisory.source_url = source_url
                existing_advisory.raw_payload = {
                    "airport_status": airport_status_value,
                    "airspace_status": airspace_status_value,
                    "airline_operations": airline_ops_value,
                }

        if official_updates and official_updates.get("summary"):
            last_updated_raw = official_updates.get("last_updated_utc")
            last_updated = None
            if isinstance(last_updated_raw, str):
                try:
                    last_updated = datetime.fromisoformat(last_updated_raw.replace("Z", "+00:00"))
                except ValueError:
                    last_updated = None

            cards = official_updates.get("cards", [])
            db.add(
                models.OfficialUpdateSnapshot(
                    summary=official_updates["summary"],
                    last_updated_utc=last_updated,
                    cards=cards,
                )
            )

        db.commit()
        logger.info("Successfully ingested offline airport data and committed to the database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to ingest airport data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # If a custom path is provided as the first argument, use it; otherwise default to data/perplexity_airports.json
    custom_path = sys.argv[1] if len(sys.argv) > 1 else "data/perplexity_airports.json"
    ingest_airports_from_file(custom_path)
