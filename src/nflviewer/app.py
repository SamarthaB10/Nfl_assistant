from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from nflviewer.models import HealthResponse

app = FastAPI(
    title="NFL Viewer API",
    description="Rank 2025 NFL regular-season matchups by watchability.",
    version="0.1.0",
)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(data_loaded=False)

