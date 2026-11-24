# API Raízes do Nordeste

API REST (back-end) da rede de lanchonetes nordestinas **Raízes do Nordeste**, com matriz, várias unidades e atendimento multicanal (APP, TOTEM, BALCÃO, PICKUP, WEB).

**Fluxo crítico (MVP):** Pedido → Pagamento mock → Atualização de status.

> Status: 🚧 em desenvolvimento. Etapa atual: setup + requisitos (23–24/11).

## Stack

| Camada | Ferramenta |
|---|---|
| Linguagem | Python 3.12+ |
| API e Swagger | FastAPI |
| Validação | Pydantic v2 |
| ORM / migrations | SQLAlchemy 2.0 / Alembic |
| Banco | PostgreSQL 16 (Docker) |
| Auth | PyJWT + argon2 (pwdlib) |
| Testes | pytest + httpx · coleção Postman |

## Requisitos

- Python 3.12 ou superior
- Docker e Docker Compose
- Git

## Como rodar

```bash
# 1. Clonar
git clone <URL_DO_REPOSITORIO>
cd raizes-nordeste-api

# 2. Variáveis de ambiente
cp .env.example .env

# 3. Subir o banco
docker compose up -d

# 4. Ambiente virtual e dependências
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 5. Migrations e seed  (disponível a partir da etapa 30/11)
# alembic upgrade head
# python -m seeds.run

# 6. Iniciar a API
uvicorn app.main:app --reload
```

## Documentação (Swagger)

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Testes

```bash
pytest -v
```

A coleção Postman fica em `docs/` (entra na etapa 08–09/12).

## Arquitetura

```
app/
├── domain/          # entidades, regras puras, enums (CanalPedido, StatusPedido)
├── application/     # casos de uso (criar_pedido, pagar_pedido...)
├── infrastructure/
│   ├── db/          # models SQLAlchemy, sessão, repositórios
│   ├── payment/     # gateway de pagamento mock (atrás de interface)
│   └── audit/       # gravação de auditoria
├── api/
│   ├── routers/     # um arquivo por recurso
│   └── schemas/     # contratos Pydantic de request/response
├── core/            # configuração
└── main.py
```

Regra central: **routers não contêm regra de negócio**. Eles recebem o request, chamam o caso de uso, e quem decide é o domínio.

## Documentos

- [Requisitos (RF/RNF e priorização)](docs/requisitos.md)
