"""A deliberately small, stateless application for the release laboratory."""
from fastapi import FastAPI, Query

app = FastAPI(title="ReleaseGuard Lab API", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/greet")
def greet(name: str = Query(default="Diego", min_length=1, max_length=60)) -> dict[str, str]:
    return {"message": f"Hola, {name}. Tu cambio está listo para ser comprobado."}
