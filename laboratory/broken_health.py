"""Fault injection, copied ONLY into the broken-health Docker target."""
from fastapi.responses import JSONResponse
from api.main import app

app.router.routes = [route for route in app.router.routes if getattr(route, "path", None) != "/health"]


@app.get("/health")
def broken_health():
    return JSONResponse(status_code=503, content={"status": "unavailable"})
