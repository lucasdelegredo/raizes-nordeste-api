# API Raízes do Nordeste

API REST (back-end) da rede de lanchonetes nordestinas **Raízes do Nordeste**, com matriz, várias unidades e atendimento multicanal (APP, TOTEM, BALCÃO, PICKUP, WEB).

**Fluxo crítico (MVP):** Pedido → Pagamento mock → Atualização de status.

> **Status:** 🚧 em desenvolvimento. Análise e modelagem concluídas (semana 1).
> **Etapa atual:** implementação da base: models, migrations e seed (a partir de 30/11).

## Progresso

| Fase | Etapa | Situação |
|---|---|---|
| Semana 1 — Análise e modelagem | Setup do projeto + requisitos | ✅ Concluída |
| | Casos de uso + feature crítica | ✅ Concluída |
| | DER + diagrama de classes + sequência | ✅ Concluída |
| | Contrato da API | ✅ Concluída |
| Semana 2 — Implementação do MVP | Base: models, migrations, seed | 🚧 Em andamento |
| | Autenticação JWT + erro padrão | ⏳ |
| | Pedidos (criação, listagem, status) | ⏳ |
| | Pagamento mock | ⏳ |
| Semana 3 — Segurança, testes e documentação | Auditoria, LGPD e fidelidade | ⏳ |
| | Coleção Postman + Swagger completo | ⏳ |
| | README final e PDF | ⏳ |

## Stack

| Camada | Ferramenta |
|---|---|
| Linguagem | Python 3.12+ (testado até o 3.14) |
| API e Swagger | FastAPI |
| Validação | Pydantic v2 |
| ORM / migrations | SQLAlchemy 2.0 / Alembic |
| Banco | PostgreSQL 16 (Docker) |
| Auth | PyJWT + argon2 (pwdlib) |
| Testes | pytest + httpx · coleção Postman |

## Requisitos

- Python 3.12 ou superior
- Docker e Docker Compose (no Windows, Docker Desktop aberto)
- Git

## Como rodar

```bash
# 1. Clonar
git clone https://github.com/lucasdelegredo/raizes-nordeste-api.git
cd raizes-nordeste-api

# 2. Variáveis de ambiente
cp .env.example .env              # Windows: copy .env.example .env

# 3. Subir o banco
docker compose up -d

# 4. Ambiente virtual e dependências
python -m venv .venv
source .venv/bin/activate         # Windows (PowerShell): .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 5. Migrations e seed  (disponível ao final da etapa de base)
# alembic upgrade head
# python -m seeds.run

# 6. Iniciar a API
uvicorn app.main:app --reload
```

Para conferir se está tudo funcionando, acesse http://localhost:8000/health. Ele deve responder `"database": "ok"`.

## Documentação da API (Swagger)

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

O Swagger é gerado automaticamente a partir do código e acompanha o [contrato da API](docs/contrato-api.md) conforme os endpoints são implementados.

## Testes

```bash
pytest -v
```

A coleção Postman ficará em `docs/` (etapa 08–09/12).

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

Regra central: **routers não contêm regra de negócio**. Eles recebem o request e chamam o caso de uso, e quem decide é o domínio.

## Documentos

| Documento | Conteúdo |
|---|---|
| [Requisitos](docs/requisitos.md) | RF e RNF, com priorização (implementado / simplificado / documentado) |
| [Casos de uso](docs/casos-de-uso.md) | Atores, diagrama, feature crítica "Realizar Pedido + Solicitar Pagamento" e regras de negócio (RN01–RN13) |
| [Modelagem](docs/modelagem.md) | DER, diagrama de classes, diagrama de sequência e decisões de modelagem |
| [Contrato da API](docs/contrato-api.md) | Rotas, perfis, exemplos de request/response, status codes, padrão de erro e plano de testes |

Diagramas em `docs/diagramas/`:

| Diagrama | Arquivo |
|---|---|
| Casos de uso | [casos-de-uso.png](docs/diagramas/casos-de-uso.png) |
| DER | [der.png](docs/diagramas/der.png) |
| Classes (domínio) | [classes.png](docs/diagramas/classes.png) |
| Sequência do fluxo crítico | [sequencia.png](docs/diagramas/sequencia.png) |
