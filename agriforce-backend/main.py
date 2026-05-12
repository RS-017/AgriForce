"""main.py — AgriForce FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.rate_limit import limiter
from routers import (
    auth,
    workers,
    jobs,
    applications,
    equipment,
    subsidies,
    forecast,
    crops,
    locations,
    admin,
    websocket,
)

app = FastAPI(
    title="AgriForce API",
    description="AI-powered agricultural labour shortage management platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate Limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
for router_module in [
    auth,
    workers,
    jobs,
    applications,
    equipment,
    subsidies,
    forecast,
    crops,
    locations,
    admin,
    websocket,
]:
    app.include_router(router_module.router)


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": "AgriForce API", "version": "1.0.0"}


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
