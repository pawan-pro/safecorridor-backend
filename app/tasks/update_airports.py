from datetime import datetime, timezone
import asyncio
import logging

from app.database import SessionLocal
from app import models
from app.perplexity_client import fetch_airport_status

logger = logging.getLogger(__name__)

async def refresh_core_airports():
    db = SessionLocal()
    try:
        core_icaos = ["OMDB", "OMDW", "OMAA", "OMSJ", "OTHH", "OOMS", "VIDP", "VABB", "LIRF", "EDDM"]
        
        logger.info(f"Starting Perplexity background sync for {len(core_icaos)} airports...")
        
        for icao in core_icaos:
            logger.info(f"Querying status for {icao}")
            
            result = await fetch_airport_status(icao)
            
            airport = db.query(models.Airport).filter(models.Airport.icao == icao).first()
            if not airport:
                logger.warning(f"Airport {icao} not found in DB, skipping.")
                continue

            status_map = {
                "OPEN": models.StatusEnum.OPEN,
                "RESTRICTED": models.StatusEnum.RESTRICTED,
                "CLOSED": models.StatusEnum.CLOSED,
                "UNKNOWN": models.StatusEnum.UNKNOWN,
            }
            api_status = result.get("status", "UNKNOWN")
            airport.status = status_map.get(api_status, models.StatusEnum.UNKNOWN)
            airport.status_reason = result.get("status_reason")
            airport.status_source = result.get("status_source_url")
            airport.status_last_updated = datetime.now(timezone.utc)

            # Insert an Advisory based off of the first piece of evidence
            evidence = result.get("evidence") or []
            if evidence:
                ev = evidence[0]
                advisory_title = ev.get("title") or f"Update for {icao}"
                
                # Check to make sure we don't accidentally insert spam from rapid-fire same exact responses
                existing_advisory = db.query(models.Advisory).filter(
                    models.Advisory.title == advisory_title,
                    models.Advisory.source_url == ev.get("url")
                ).first()
                
                if not existing_advisory:
                    advisory = models.Advisory(
                        source_type=models.AdvisorySourceType.AIRPORT, 
                        source_name=result.get("status_source_name", "Perplexity Aggregated"),
                        source_url=ev.get("url"),
                        title=advisory_title,
                        summary=ev.get("snippet", result.get("status_reason")),
                        airports_icao=[icao],
                    )
                    db.add(advisory)
            
            # Simple back-off
            await asyncio.sleep(2) 

        db.commit()
        logger.info("Finished syncing airport status in background.")
    except Exception as e:
         db.rollback()
         logger.error(f"Failed background sync: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(refresh_core_airports())
