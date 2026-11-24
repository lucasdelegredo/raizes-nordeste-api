"""Ponto de entrada da API. Aqui só se monta a aplicação: nenhuma regra de negócio."""
from fastapi import FastAPI

from app.api.routers import health
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API REST da rede de lanchonetes **Raízes do Nordeste**.\n\n"
        "Fluxo crítico (MVP): Pedido → Pagamento mock → Atualização de status."
    ),
)

app.include_router(health.router)
