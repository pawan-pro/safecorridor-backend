import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import airports, routes, advisories, admin, official_updates, flights
from .db_migrations import ensure_airport_columns

try:
    from .routers import live_agent
except ImportError:
    live_agent = None

Base.metadata.create_all(bind=engine)
ensure_airport_columns()

app = FastAPI(
    title="SafeCorridor API",
    description="API for finding plausible air routes during Gulf airspace closures.",
    version="1.0.0"
)

raw_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
allow_credentials = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["http://localhost:3000"],
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(airports.router, prefix="/api/airports", tags=["Airports"])
app.include_router(routes.router, prefix="/api/routes", tags=["Routes"])
app.include_router(advisories.router, prefix="/api/advisories", tags=["Advisories"])
app.include_router(official_updates.router, prefix="/api/official-updates", tags=["Official Updates"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(flights.router, prefix="/api/flights", tags=["Flights"])
if live_agent is not None:
    app.include_router(live_agent.router, prefix="/api/live-agent", tags=["Live Agent"])

@app.get("/api/health")
def read_root():
    return {"status": "ok", "service": "safecorridor-api"}
