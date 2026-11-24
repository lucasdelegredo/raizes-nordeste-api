"""Health check: confirma que a API está de pé e que o banco responde."""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas.health import HealthResponse
from app.core.config import get_settings
from app.infrastructure.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verifica a saúde da API e a conexão com o banco",
    responses={
        200: {"description": "API e banco operacionais"},
        503: {"description": "API no ar, mas o banco está indisponível"},
    },
)
def health(response: Response, db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "indisponivel"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="ok" if db_status == "ok" else "degradado",
        database=db_status,
        version=get_settings().APP_VERSION,
    )
