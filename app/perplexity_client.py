import os
import json
from datetime import datetime, timezone
import httpx
from openai import AsyncOpenAI
from dotenv import load_dotenv
import asyncio
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# We can use the OpenAI client configured for Perplexity's base URL and API key
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

async def fetch_airport_status(icao: str) -> dict:
    """
    Call Perplexity API with the meta-prompt and parse the JSON result.
    Uses the modern recommended chat completions approach with Perplexity.
    """
    meta_prompt = f"""
You are an aviation operations assistant helping a travel advisory system during Middle East airspace closures.
Task: For the airport with ICAO code {icao}, determine its current operational status for commercial passenger flights today, and summarize only from reliable, recent sources (airport operator, civil aviation, major airlines, major news).

In your reasoning, check for:
- Whether the airport is open, partially restricted, or closed for regular passenger flights.
- Whether the closure is due to regional airspace restrictions, security incidents, or weather.
- Any explicit statements about suspensions, resumptions, or diversions.

Respond ONLY in strict JSON with this shape (no extra keys, no commentary):
{{
  "icao": "{icao}",
  "status": "OPEN | RESTRICTED | CLOSED | UNKNOWN",
  "status_reason": "short human-readable explanation (max 280 characters)",
  "status_source_url": "https://example.com/preferred_source",
  "status_source_name": "Airport / regulator / airline / news outlet name",
  "last_checked_utc": "ISO 8601 timestamp (UTC)",
  "evidence": [
    {{
      "title": "string",
      "url": "string",
      "snippet": "1-2 sentence evidence from the source"
    }}
  ]
}}
If information is contradictory or unclear, set "status": "UNKNOWN" and explain the uncertainty in status_reason.
""".strip()

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": "You are a highly capable and exact JSON-parsing assistant. You answer only with raw JSON code."},
            {"role": "user", "content": meta_prompt}
        ],
        "max_tokens": 2000
    }
    
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
        raw_content = data["choices"][0]["message"]["content"]
        raw_content = raw_content.replace('```json', '').replace('```', '').strip()
        
        parsed = json.loads(raw_content)
        return parsed
    except Exception as e:
        logger.error(f"Error fetching status from Perplexity for {icao}: {e}")
        # Return fallback on error
        return {
            "icao": icao,
            "status": "UNKNOWN",
            "status_reason": f"Failed to fetch updates dynamically via API. Reason: {str(e)}",
            "evidence": []
        }

if __name__ == "__main__":
    # Test script utility
    import asyncio
    async def main():
        res = await fetch_airport_status("OOMS")
        import pprint
        pprint.pprint(res)
    asyncio.run(main())
