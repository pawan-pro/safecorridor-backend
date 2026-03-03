import uuid
from datetime import datetime, timezone
import sys
import os

# Add the parent directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Base, engine
from app import models


def upsert_airport(db, icao, **kwargs):
    obj = db.query(models.Airport).filter_by(icao=icao).first()
    if obj is None:
        obj = models.Airport(icao=icao, **kwargs)
        db.add(obj)
    else:
        for k, v in kwargs.items():
            setattr(obj, k, v)
    return obj


def seed_airports(db):
    now = datetime.now(timezone.utc)

    # --- UAE & GCC hubs: suspended / heavily restricted ---
    upsert_airport(
        db,
        icao="OMDB",
        iata="DXB",
        name="Dubai International Airport",
        city="Dubai",
        country="United Arab Emirates",
        is_hub=True,
        status=models.StatusEnum.CLOSED,
        status_reason=(
            "UAE commercial airports currently non-operational or under severe restrictions for "
            "regular traffic due to Middle East airspace closures."
        ),
        status_source="https://traveltourister.com/news/dubai-airport-open-today-march-2-2026-emirates-flights-resume-suspended-dxb-live-update/",
        status_last_updated=now,
    )

    upsert_airport(
        db,
        icao="OMDW",
        iata="DWC",
        name="Al Maktoum International Airport",
        city="Dubai",
        country="United Arab Emirates",
        is_hub=True,
        status=models.StatusEnum.CLOSED,
        status_reason=(
            "Al Maktoum International subject to the same UAE-wide airspace suspension affecting "
            "Dubai hubs."
        ),
        status_source="https://traveltourister.com/news/dubai-airport-open-today-march-2-2026-emirates-flights-resume-suspended-dxb-live-update/",
        status_last_updated=now,
    )

    upsert_airport(
        db,
        icao="OMAA",
        iata="AUH",
        name="Zayed International Airport",
        city="Abu Dhabi",
        country="United Arab Emirates",
        is_hub=True,
        status=models.StatusEnum.CLOSED,
        status_reason=(
            "Departures from Abu Dhabi halted amid Gulf airspace closures and safety concerns."
        ),
        status_source="https://www.visahq.com/news/2026-03-01/ae/etihad-airways-grounds-all-abu-dhabi-departures-as-gulf-airspace-shuts/",
        status_last_updated=now,
    )

    upsert_airport(
        db,
        icao="OMSJ",
        iata="SHJ",
        name="Sharjah International Airport",
        city="Sharjah",
        country="United Arab Emirates",
        is_hub=True,
        status=models.StatusEnum.CLOSED,
        status_reason=(
            "Sharjah operations are disrupted in line with UAE airspace closures hitting all major hubs."
        ),
        status_source="https://adept.travel/news/2026-03-01-middle-east-airspace-closures-hit-dubai-doha-hubs",
        status_last_updated=now,
    )

    upsert_airport(
        db,
        icao="OTHH",
        iata="DOH",
        name="Hamad International Airport",
        city="Doha",
        country="Qatar",
        is_hub=True,
        status=models.StatusEnum.CLOSED,
        status_reason=(
            "Key Gulf hub affected by regional airspace shutdown, with wide-scale cancellations."
        ),
        status_source="https://adept.travel/news/2026-03-01-middle-east-airspace-closures-hit-dubai-doha-hubs",
        status_last_updated=now,
    )

    # --- Oman: Muscat as operational corridor to India ---
    upsert_airport(
        db,
        icao="OOMS",
        iata="MCT",
        name="Muscat International Airport",
        city="Muscat",
        country="Oman",
        is_hub=True,
        status=models.StatusEnum.OPEN,
        status_reason=(
            "Oman Airports report ongoing operations at Muscat with disruptions; flights to India "
            "continue despite regional Gulf cancellations."
        ),
        status_source="https://www.omanobserver.om/article/1185225/oman/flight-cancellations-in-gcc-airports-to-continue-on-monday",
        status_last_updated=now,
    )

    # --- India hubs (open; rerouting around Middle East) ---
    upsert_airport(
        db,
        icao="VIDP",
        iata="DEL",
        name="Indira Gandhi International Airport",
        city="Delhi",
        country="India",
        is_hub=True,
        status=models.StatusEnum.OPEN,
        status_reason=(
            "India hub operating; long-haul flights are rerouting via safer corridors and Europe."
        ),
        status_source="https://www.hindustantimes.com/india-news/alternative-routes-technical-stops-airlines-rerouting-services-to-operate-flights-to-us-europe-amid-iran-conflict-101710925716710.html",
        status_last_updated=now,
    )

    upsert_airport(
        db,
        icao="VABB",
        iata="BOM",
        name="Chhatrapati Shivaji Maharaj International Airport",
        city="Mumbai",
        country="India",
        is_hub=True,
        status=models.StatusEnum.OPEN,
        status_reason=(
            "Mumbai remains open; India–US flights are being rerouted via Europe to bypass "
            "Middle East airspace."
        ),
        status_source="https://www.indianeagle.com/travelbeats/usa-india-flights-rerouted-bypassing-iranian-airspace/",
        status_last_updated=now,
    )

    # --- Europe hubs used in reroutes ---
    upsert_airport(
        db,
        icao="LIRF",
        iata="FCO",
        name="Leonardo da Vinci–Fiumicino Airport",
        city="Rome",
        country="Italy",
        is_hub=True,
        status=models.StatusEnum.OPEN,
        status_reason=(
            "Rome is being used as a technical stop and hub on rerouted India–US flights "
            "avoiding Middle East airspace."
        ),
        status_source="https://www.indianeagle.com/travelbeats/usa-india-flights-rerouted-bypassing-iranian-airspace/",
        status_last_updated=now,
    )

    upsert_airport(
        db,
        icao="EDDM",
        iata="MUC",
        name="Munich International Airport",
        city="Munich",
        country="Germany",
        is_hub=True,
        status=models.StatusEnum.OPEN,
        status_reason=(
            "Munich and other European hubs are absorbing rerouted long-haul traffic around "
            "the Gulf closures."
        ),
        status_source="https://www.travelandtourworld.com/news/article/middle-east-airspace-shutdown-sparks-global-travel-chaos-tens-of-thousands-of-flights-cancelled/",
        status_last_updated=now,
    )

    db.commit()


def seed_route_patterns(db):
    now = datetime.now(timezone.utc)

    def add_route(origin_region, destination_region, via_list, status, reason):
        # Prevent duplications for simplicity in re-runs:
        existing = db.query(models.RoutePattern).filter_by(
            origin_region=origin_region,
            destination_region=destination_region,
            status=status
        ).first()
        
        if not existing:
            rp = models.RoutePattern(
                origin_region=origin_region,
                origin_airport_icao=None,
                destination_region=destination_region,
                destination_airport_icao=None,
                via_airports_icao=via_list,
                status=status,
                reason=reason,
                last_updated=now,
            )
            db.add(rp)

    # --- UAE → India ---

    add_route(
        origin_region="UAE",
        destination_region="India-All",
        via_list=[],
        status=models.RouteStatusEnum.UNAVAILABLE,
        reason=(
            "Direct UAE–India services via UAE hubs are unavailable while Dubai, Abu Dhabi and "
            "other UAE airports are suspended or severely restricted."
        ),
    )

    add_route(
        origin_region="UAE-Road",
        destination_region="India-All",
        via_list=["OOMS"],
        status=models.RouteStatusEnum.RECOMMENDED,
        reason=(
            "For travellers able to drive or take ground transport from the UAE to Oman via land "
            "borders (e.g., Hatta–Al Wajajah), Muscat airport offers onward flights to India."
        ),
    )

    add_route(
        origin_region="UAE",
        destination_region="India-South",
        via_list=["OOMS"],
        status=models.RouteStatusEnum.RECOMMENDED,
        reason=(
            "With UAE hubs disrupted, routing via Muscat offers a plausible corridor to "
            "southern India where flights are still operating with disruptions."
        ),
    )

    add_route(
        origin_region="UAE",
        destination_region="India-West",
        via_list=["OOMS"],
        status=models.RouteStatusEnum.RECOMMENDED,
        reason=(
            "Muscat functions as an alternate hub for western India routes while Gulf hubs "
            "like Dubai and Doha remain affected by closures."
        ),
    )

    # --- Gulf (excluding UAE) → India ---

    add_route(
        origin_region="Gulf-Other",
        destination_region="India-All",
        via_list=["OOMS"],
        status=models.RouteStatusEnum.RECOMMENDED,
        reason=(
            "Multiple Gulf hubs including Dubai and Doha are disrupted; Oman’s Muscat airport "
            "stays open with flights to India, making it a key diversion hub."
        ),
    )

    # --- Gulf → US (via Europe) ---

    add_route(
        origin_region="Gulf-All",
        destination_region="US-East",
        via_list=["LIRF", "EDDM"],
        status=models.RouteStatusEnum.RECOMMENDED,
        reason=(
            "With Gulf hubs restricted, travellers may connect through European hubs like Rome "
            "and Munich en route to the US East Coast, mirroring current India–US rerouting."
        ),
    )

    add_route(
        origin_region="Gulf-All",
        destination_region="US-West",
        via_list=["LIRF", "EDDM"],
        status=models.RouteStatusEnum.DISCOURAGED,
        reason=(
            "Gulf–US West Coast itineraries via Europe are possible but face higher disruption "
            "risk and limited capacity; treat as secondary options."
        ),
    )

    # --- Europe → India ---

    add_route(
        origin_region="Europe-West",
        destination_region="India-All",
        via_list=[],
        status=models.RouteStatusEnum.RECOMMENDED,
        reason=(
            "Europe–India flights largely continue with altered routings that bypass closed "
            "Middle East airspace; this remains a primary corridor subject to airline disruptions."
        ),
    )

    add_route(
        origin_region="Europe-West",
        destination_region="India-All",
        via_list=["LIRF", "EDDM"],
        status=models.RouteStatusEnum.RECOMMENDED,
        reason=(
            "Some Europe–India flows are channelled via Rome and Munich as carriers adjust to "
            "Gulf closures."
        ),
    )

    # --- India → US (via Europe) ---

    add_route(
        origin_region="India-All",
        destination_region="US-East",
        via_list=["LIRF", "EDDM"],
        status=models.RouteStatusEnum.RECOMMENDED,
        reason=(
            "Airlines operating India–US flights are rerouting via European hubs such as Rome "
            "and Munich with technical stops to avoid Middle East airspace."
        ),
    )

    add_route(
        origin_region="India-All",
        destination_region="US-West",
        via_list=["LIRF", "EDDM"],
        status=models.RouteStatusEnum.DISCOURAGED,
        reason=(
            "India–US West Coast routings via Europe are more vulnerable to extended flight "
            "times and cancellations; confirm on a case-by-case basis."
        ),
    )

    db.commit()


def seed_advisories_from_airports(db):
    airports = db.query(models.Airport).all()
    now = datetime.now(timezone.utc)

    for airport in airports:
        title = f"Status update for {airport.icao}"
        exists = db.query(models.Advisory).filter(
            models.Advisory.title == title,
            models.Advisory.source_url == airport.status_source,
        ).first()

        if exists:
            continue

        db.add(
            models.Advisory(
                source_type=models.AdvisorySourceType.AIRPORT,
                source_name="SafeCorridor Seed Data",
                source_url=airport.status_source,
                title=title,
                summary=airport.status_reason or f"{airport.name} currently marked as {airport.status.value}.",
                airports_icao=[airport.icao],
                created_at=now,
            )
        )

    db.commit()


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_airports(db)
        seed_route_patterns(db)
        seed_advisories_from_airports(db)
        print("Database seeded successfully.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
