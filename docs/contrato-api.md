# Contrato da API — Raízes do Nordeste

Versão 0.4 — 25/11/2026 · Base URL local: `http://localhost:8000`

Este documento é o **acordo entre o back-end e os clientes** (App, Totem, Web, Balcão). Ele foi definido **antes da implementação** e serve de referência para o código (schemas Pydantic), para o Swagger (`/docs`), para a coleção Postman e para a seção "API e endpoints" do PDF.

Ele segue as regras de negócio de [`casos-de-uso.md`](casos-de-uso.md) (RN01–RN13) e o modelo de [`modelagem.md`](modelagem.md).

---

## 1. Convenções gerais

| Item | Padrão |
|---|---|
| Formato | JSON (`Content-Type: application/json`), UTF-8 |
| Nomes de campos | **camelCase** no JSON (`canalPedido`, `unidadeId`). No banco, snake_case (`canal_pedido`); a conversão é feita pelos schemas Pydantic. |
| Rotas | Substantivos no plural (`/pedidos`); ID no caminho (`/pedidos/{id}`); filtros na query (`?status=PAGO`) |
| Ações que não são CRUD | Sub-recurso no plural (`POST /pedidos/{id}/cancelamentos`, `POST /fidelidade/resgates`) |
| Datas | ISO 8601 em UTC: `2026-12-03T14:20:00Z` |
| Valores monetários | Número com 2 casas decimais (`31.80`), em reais |
| IDs | Inteiros |
| Enums | Texto em MAIÚSCULAS, exatamente como no domínio (`AGUARDANDO_PAGAMENTO`) |
| Campos ausentes vs. nulos | Campo opcional sem valor é retornado como `null`; nunca é omitido da resposta |
| Dados sensíveis | **Nunca** retornados: `senhaHash`, payloads brutos do gateway para o cliente, dados de outros usuários |

### 1.1 Cabeçalhos

| Cabeçalho | Onde | Uso |
|---|---|---|
| `Authorization: Bearer <token>` | Request | Obrigatório em todas as rotas, exceto as marcadas como **públicas** |
| `Idempotency-Key: <uuid>` | Request | Obrigatório em `POST /pagamentos` (RN08) |
| `X-Request-Id` | Request (opcional) / Response | Identificador da requisição. Se o cliente não enviar, a API gera um. Aparece também no corpo dos erros e nos registros de auditoria |

### 1.2 Status codes

| Código | Quando |
|---|---|
| `200 OK` | Consulta ou atualização com sucesso; repetição idempotente de pagamento |
| `201 Created` | Recurso criado (pedido, pagamento, movimentação, usuário…) |
| `204 No Content` | Sucesso sem corpo (remoção, revogação) |
| `400 Bad Request` | JSON malformado (não é possível ler o corpo) |
| `401 Unauthorized` | Token ausente, inválido ou expirado; login com credenciais inválidas |
| `403 Forbidden` | Autenticado, mas sem permissão (perfil, unidade, recurso de outro usuário, falta de consentimento) |
| `404 Not Found` | Recurso inexistente |
| `409 Conflict` | Violação de regra de negócio ou de estado (estoque, transição, duplicidade) |
| `422 Unprocessable Entity` | Validação de campos (obrigatório ausente, tipo, formato, faixa de valores) |
| `502 Bad Gateway` | Falha ou timeout do gateway de pagamento |

**Regra de desempate entre 403 e 409 nas transições de status:** se a transição **não existe** na máquina de estados (ex.: `PRONTO → PAGO`), a resposta é `409 TRANSICAO_INVALIDA`. Se ela existe, mas **o perfil não pode executá-la** (ex.: `ATENDENTE` tentando `PAGO → EM_PREPARO`), a resposta é `403 ACESSO_NEGADO`.

---

## 2. Autenticação e perfis

- Login em `POST /auth/login` devolve um **JWT** (HS256) válido por 60 minutos.
- Claims do token: `sub` (id do usuário), `perfil`, `unidadeId` (ou `null`), `exp`.
- O token **não** carrega nome nem e-mail (minimização).
- Senhas são armazenadas apenas como hash (argon2).

| Perfil | Escopo |
|---|---|
| `CLIENTE` | Apenas os próprios dados, pedidos, pagamentos, consentimentos e pontos |
| `ATENDENTE` | Pedidos da **própria unidade** |
| `COZINHA` | Pedidos da **própria unidade** (fila de preparo) |
| `GERENTE` | Pedidos, estoque e cardápio da **própria unidade**; auditoria |
| `ADMIN` | Toda a rede: unidades, produtos, funcionários, auditoria |

---

## 3. Paginação

Toda listagem aceita `page` (padrão `1`, mínimo `1`) e `limit` (padrão `10`, mínimo `1`, máximo `100`). Valores fora da faixa → `422 VALIDACAO`.

Formato da resposta paginada:

```json
{
  "items": [ ... ],
  "page": 1,
  "limit": 10,
  "totalItems": 57,
  "totalPages": 6
}
```

---

## 4. Padrão de erro

**Todas** as falhas, inclusive 401, 403, 404 e 422 gerados pelo próprio framework, seguem o formato abaixo:

```json
{
  "error": "ESTOQUE_INSUFICIENTE",
  "message": "Não há quantidade suficiente para um ou mais itens.",
  "details": [
    { "field": "itens[0].quantidade", "issue": "Disponível: 1" }
  ],
  "timestamp": "2026-12-01T12:00:00Z",
  "path": "/pedidos",
  "requestId": "7f3c2a9e-5b1d-4c8e-9a2f-1d6e8b4c3a10"
}
```

| Campo | Descrição |
|---|---|
| `error` | Código estável, em MAIÚSCULAS, para o cliente tratar por programa |
| `message` | Texto legível em português, para exibir ao usuário |
| `details` | Lista de problemas por campo (pode ser vazia `[]`) |
| `timestamp` | Momento do erro, em UTC |
| `path` | Rota chamada |
| `requestId` | Mesmo valor do cabeçalho `X-Request-Id` |

### 4.1 Catálogo de códigos de erro

| HTTP | `error` | Situação |
|---|---|---|
| 400 | `REQUISICAO_MALFORMADA` | Corpo não é um JSON válido |
| 401 | `NAO_AUTENTICADO` | Token ausente, inválido ou expirado |
| 401 | `CREDENCIAIS_INVALIDAS` | E-mail ou senha incorretos no login (mensagem genérica, sem dizer qual dos dois) |
| 403 | `ACESSO_NEGADO` | Perfil sem permissão, unidade diferente ou recurso de outro usuário |
| 403 | `CONSENTIMENTO_NECESSARIO` | Fidelidade usada sem consentimento ativo (RN13) |
| 404 | `RECURSO_NAO_ENCONTRADO` | Genérico (rota com ID inexistente) |
| 404 | `UNIDADE_NAO_ENCONTRADA` | Unidade inexistente ou inativa |
| 404 | `PRODUTO_NAO_ENCONTRADO` | Produto inexistente ou fora do cardápio da unidade |
| 404 | `PEDIDO_NAO_ENCONTRADO` | Pedido inexistente |
| 409 | `EMAIL_JA_CADASTRADO` | Cadastro com e-mail já usado |
| 409 | `ESTOQUE_INSUFICIENTE` | Saldo insuficiente no pedido ou na saída manual |
| 409 | `TRANSICAO_INVALIDA` | Transição de status inexistente na máquina de estados |
| 409 | `PEDIDO_NAO_AGUARDA_PAGAMENTO` | Pagamento de pedido que não está em `AGUARDANDO_PAGAMENTO` |
| 409 | `PEDIDO_NAO_CANCELAVEL` | Cancelamento a partir de um status que não permite |
| 409 | `IDEMPOTENCY_KEY_CONFLITO` | Mesma chave usada para outro pedido |
| 409 | `PONTOS_INSUFICIENTES` | Resgate maior que o saldo |
| 409 | `PRODUTO_JA_NO_CARDAPIO` | Produto já adicionado ao cardápio da unidade |
| 422 | `VALIDACAO` | Campo obrigatório ausente, tipo ou formato inválido, valor fora da faixa |
| 422 | `CANAL_INVALIDO_PARA_PERFIL` | Canal incompatível com o perfil (RN03) |
| 502 | `GATEWAY_INDISPONIVEL` | Timeout ou falha do gateway de pagamento |
| 500 | `ERRO_INTERNO` | Erro inesperado (sem detalhes técnicos na resposta; detalhe só no log) |

Exemplo de `422` para `canalPedido` ausente (T04):

```json
{
  "error": "VALIDACAO",
  "message": "Um ou mais campos são inválidos.",
  "details": [ { "field": "canalPedido", "issue": "Campo obrigatório" } ],
  "timestamp": "2026-12-03T14:20:00Z",
  "path": "/pedidos",
  "requestId": "…"
}
```

---

## 5. Endpoints por recurso

### Visão geral

| Recurso | Método e rota | Perfis |
|---|---|---|
| Health | `GET /health` | público |
| Auth | `POST /auth/login` | público |
| Usuários | `POST /usuarios` | público |
| | `GET /usuarios/me` | autenticado |
| | `POST /usuarios/funcionarios` | ADMIN |
| | `GET /usuarios/me/consentimentos` | CLIENTE |
| | `POST /usuarios/me/consentimentos` | CLIENTE |
| | `DELETE /usuarios/me/consentimentos/{finalidade}` | CLIENTE |
| Unidades | `GET /unidades` | autenticado |
| | `GET /unidades/{id}` | autenticado |
| | `POST /unidades` | ADMIN |
| | `PATCH /unidades/{id}` | ADMIN |
| Cardápio | `GET /unidades/{id}/cardapio` | autenticado |
| | `POST /unidades/{id}/cardapio` | ADMIN |
| | `PATCH /unidades/{id}/cardapio/{produtoId}` | ADMIN, GERENTE (própria unidade) |
| Produtos | `GET /produtos` | autenticado |
| | `GET /produtos/{id}` | autenticado |
| | `POST /produtos` | ADMIN |
| | `PUT /produtos/{id}` | ADMIN |
| | `DELETE /produtos/{id}` | ADMIN |
| Estoque | `GET /estoque` | GERENTE (própria unidade), ADMIN |
| | `POST /estoque/movimentacoes` | GERENTE (própria unidade), ADMIN |
| | `GET /estoque/movimentacoes` | GERENTE (própria unidade), ADMIN |
| **Pedidos** | **`POST /pedidos`** | CLIENTE, ATENDENTE |
| | **`GET /pedidos`** | todos (com escopo por perfil) |
| | `GET /pedidos/{id}` | dono ou funcionário da unidade, ADMIN |
| | **`PATCH /pedidos/{id}/status`** | COZINHA, ATENDENTE (conforme RN11) |
| | `POST /pedidos/{id}/cancelamentos` | CLIENTE (dono), ATENDENTE, GERENTE (conforme RN11) |
| | `GET /pedidos/{id}/pagamentos` | dono ou funcionário da unidade, ADMIN |
| **Pagamentos** | **`POST /pagamentos`** | CLIENTE (dono), ATENDENTE (unidade do pedido) |
| | `GET /pagamentos/{id}` | dono ou funcionário da unidade, ADMIN |
| Fidelidade | `GET /fidelidade/saldo` | CLIENTE com consentimento |
| | `GET /fidelidade/extrato` | CLIENTE com consentimento |
| | `POST /fidelidade/resgates` | CLIENTE com consentimento |
| Auditoria | `GET /auditoria` | GERENTE, ADMIN |

Em destaque: os endpoints do **fluxo crítico**.

---

### 5.1 Health

#### `GET /health` — Verifica a API e a conexão com o banco
**Auth:** pública

**200**
```json
{ "status": "ok", "database": "ok", "version": "0.1.0" }
```
**503** — banco indisponível: `{ "status": "degradado", "database": "indisponivel", "version": "0.1.0" }`

> Única rota que não usa o formato de erro padrão, porque é uma sonda de monitoramento, e não um erro da requisição.

---

### 5.2 Auth

#### `POST /auth/login` — Autentica e emite o token de acesso
**Auth:** pública

**Request**
```json
{ "email": "cliente@raizes.com", "senha": "Senha@123" }
```
**200**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "usuario": { "id": 5, "nome": "Maria Cliente", "perfil": "CLIENTE", "unidadeId": null }
}
```
**Erros:** `401 CREDENCIAIS_INVALIDAS` · `422 VALIDACAO` (e-mail em formato inválido, campo ausente)

> *Refresh* e *logout* ficam **documentados como proposta**: o token expira em 60 minutos e o cliente faz login novamente. Logout com revogação exigiria uma lista de tokens bloqueados.

---

### 5.3 Usuários e consentimento

#### `POST /usuarios` — Cadastra um cliente
**Auth:** pública · sempre cria com perfil `CLIENTE`

**Request**
```json
{ "nome": "Maria Cliente", "email": "maria@exemplo.com", "senha": "Senha@123" }
```
Regras: `nome` com 2 a 120 caracteres; `email` válido; `senha` com no mínimo 8 caracteres, contendo letra e número.

**201**
```json
{ "id": 12, "nome": "Maria Cliente", "email": "maria@exemplo.com", "perfil": "CLIENTE", "criadoEm": "2026-12-02T10:00:00Z" }
```
**Erros:** `409 EMAIL_JA_CADASTRADO` · `422 VALIDACAO` (T05: e-mail inválido)

#### `GET /usuarios/me` — Dados do usuário logado
**Auth:** autenticado · **200**: mesmo formato do cadastro, mais `unidadeId`. **Erros:** `401`

#### `POST /usuarios/funcionarios` — Cadastra um funcionário
**Auth:** ADMIN

**Request**
```json
{ "nome": "João Atendente", "email": "joao@raizes.com", "senha": "Senha@123", "perfil": "ATENDENTE", "unidadeId": 1 }
```
Regras: `perfil` ∈ {ATENDENTE, COZINHA, GERENTE, ADMIN}; `unidadeId` obrigatório para ATENDENTE, COZINHA e GERENTE, e deve ser `null` para ADMIN.

**201**: dados do usuário, sem senha. **Erros:** `401` · `403` · `404 UNIDADE_NAO_ENCONTRADA` · `409 EMAIL_JA_CADASTRADO` · `422 VALIDACAO`

#### `GET /usuarios/me/consentimentos` — Lista os consentimentos do cliente
**Auth:** CLIENTE

**200**
```json
[
  { "finalidade": "FIDELIDADE", "versaoTermo": "1.0", "concedidoEm": "2026-12-02T10:05:00Z", "revogadoEm": null, "ativo": true }
]
```

#### `POST /usuarios/me/consentimentos` — Concede consentimento
**Auth:** CLIENTE

**Request**
```json
{ "finalidade": "FIDELIDADE", "versaoTermo": "1.0" }
```
**201**: o consentimento criado. Se já existir um consentimento ativo para a mesma finalidade e versão, retorna **200** com o existente (operação idempotente).
**Erros:** `401` · `403` · `422 VALIDACAO` (finalidade fora de FIDELIDADE ou MARKETING)

#### `DELETE /usuarios/me/consentimentos/{finalidade}` — Revoga consentimento
**Auth:** CLIENTE · **204**. O registro **não é apagado**: recebe `revogadoEm`, o que preserva a evidência exigida pela LGPD. Os pontos acumulados ficam congelados até um novo consentimento.
**Erros:** `401` · `403` · `404 RECURSO_NAO_ENCONTRADO` (não há consentimento ativo para a finalidade)

---

### 5.4 Unidades e cardápio

#### `GET /unidades` — Lista unidades ativas
**Auth:** autenticado · **Query:** `cidade`, `uf`, `page`, `limit`

**200** (paginado)
```json
{
  "items": [ { "id": 1, "nome": "Raízes Boa Viagem", "cidade": "Recife", "uf": "PE", "tipo": "COMPLETA", "ativa": true } ],
  "page": 1, "limit": 10, "totalItems": 3, "totalPages": 1
}
```

#### `GET /unidades/{id}` — Detalha uma unidade
**200**: objeto da unidade · **Erros:** `401` · `404 UNIDADE_NAO_ENCONTRADA`

#### `POST /unidades` — Cria unidade
**Auth:** ADMIN

**Request**
```json
{ "nome": "Raízes Fortaleza Centro", "cidade": "Fortaleza", "uf": "CE", "tipo": "REDUZIDA" }
```
**201**: unidade criada (`ativa: true`) · **Erros:** `401` · `403` · `422`

#### `PATCH /unidades/{id}` — Atualiza dados ou desativa
**Auth:** ADMIN · **Request:** qualquer subconjunto de `nome`, `cidade`, `uf`, `tipo`, `ativa` · **200** · **Erros:** `401` · `403` · `404` · `422`

#### `GET /unidades/{id}/cardapio` — Cardápio da unidade
**Auth:** autenticado · **Query:** `categoria`, `somenteDisponiveis` (padrão `true`), `page`, `limit`

**200** (paginado)
```json
{
  "items": [
    { "produtoId": 10, "nome": "Tapioca de carne de sol", "categoria": "TAPIOCAS", "preco": 15.90, "disponivel": true },
    { "produtoId": 14, "nome": "Pamonha", "categoria": "SAZONAIS", "preco": 8.50, "disponivel": false }
  ],
  "page": 1, "limit": 10, "totalItems": 2, "totalPages": 1
}
```
`disponivel` só é `true` quando o item está liberado no cardápio **e** há saldo em estoque.
**Erros:** `401` · `404 UNIDADE_NAO_ENCONTRADA`

#### `POST /unidades/{id}/cardapio` — Adiciona produto ao cardápio
**Auth:** ADMIN

**Request**
```json
{ "produtoId": 10, "preco": 15.90, "disponivel": true }
```
Se `preco` for omitido, usa o `precoBase` do produto.
**201** · **Erros:** `401` · `403` · `404 UNIDADE_NAO_ENCONTRADA` / `PRODUTO_NAO_ENCONTRADO` · `409 PRODUTO_JA_NO_CARDAPIO` · `422`

#### `PATCH /unidades/{id}/cardapio/{produtoId}` — Altera preço ou disponibilidade
**Auth:** ADMIN (preço e disponibilidade); GERENTE da própria unidade (**somente** `disponivel`)

**Request**
```json
{ "disponivel": false }
```
**200** · **Erros:** `401` · `403` (GERENTE tentando alterar o preço ou outra unidade) · `404` · `422`

---

### 5.5 Produtos (catálogo da rede)

#### `GET /produtos` — Lista produtos
**Auth:** autenticado · **Query:** `nome` (busca parcial), `categoria`, `page`, `limit`

**200** (paginado)
```json
{
  "items": [ { "id": 10, "nome": "Tapioca de carne de sol", "descricao": "Com queijo coalho", "categoria": "TAPIOCAS", "precoBase": 15.90, "ativo": true } ],
  "page": 1, "limit": 10, "totalItems": 18, "totalPages": 2
}
```

#### `GET /produtos/{id}` — Detalha produto
**200** · **Erros:** `401` · `404 PRODUTO_NAO_ENCONTRADO`

#### `POST /produtos` — Cria produto
**Auth:** ADMIN

**Request**
```json
{ "nome": "Cuscuz recheado", "descricao": "Com ovo e queijo", "categoria": "CUSCUZ", "precoBase": 18.00 }
```
Regras: `precoBase` > 0; `nome` com 2 a 120 caracteres.
**201** · **Erros:** `401` · `403` · `422`

#### `PUT /produtos/{id}` — Substitui os dados do produto
**Auth:** ADMIN · **Request:** mesmo corpo do `POST` · **200** · **Erros:** `401` · `403` · `404` · `422`

#### `DELETE /produtos/{id}` — Desativa produto
**Auth:** ADMIN · **204**. A exclusão é **lógica** (`ativo = false`), porque o produto pode estar em pedidos antigos. Ele deixa de aparecer nos cardápios.
**Erros:** `401` · `403` · `404`

---

### 5.6 Estoque

#### `GET /estoque` — Saldo por unidade
**Auth:** GERENTE (própria unidade), ADMIN · **Query:** `unidadeId` (**obrigatório** para ADMIN; para GERENTE, assume a própria unidade), `produtoId`, `page`, `limit`

**200** (paginado)
```json
{
  "items": [ { "unidadeId": 1, "produtoId": 10, "produtoNome": "Tapioca de carne de sol", "quantidade": 25, "atualizadoEm": "2026-12-03T14:20:00Z" } ],
  "page": 1, "limit": 10, "totalItems": 12, "totalPages": 2
}
```
**Erros:** `401` · `403` (outra unidade) · `422` (ADMIN sem `unidadeId`)

#### `POST /estoque/movimentacoes` — Registra entrada ou saída manual
**Auth:** GERENTE (própria unidade), ADMIN

**Request**
```json
{ "unidadeId": 1, "produtoId": 10, "tipo": "ENTRADA", "quantidade": 30, "motivo": "Reposição semanal" }
```
Regras: `tipo` ∈ {ENTRADA, SAIDA} (RESERVA e ESTORNO_RESERVA são exclusivos do sistema); `quantidade` inteira > 0; `motivo` obrigatório para SAIDA. Gera auditoria `ESTOQUE_MOVIMENTADO`.

**201**
```json
{ "id": 87, "unidadeId": 1, "produtoId": 10, "tipo": "ENTRADA", "quantidade": 30, "saldoAtual": 55, "motivo": "Reposição semanal", "criadoEm": "2026-12-03T09:00:00Z" }
```
**Erros:** `401` · `403` (T03: CLIENTE; ou GERENTE de outra unidade) · `404` · `409 ESTOQUE_INSUFICIENTE` (saída maior que o saldo) · `422`

#### `GET /estoque/movimentacoes` — Histórico de movimentações
**Auth:** GERENTE (própria unidade), ADMIN · **Query:** `unidadeId`, `produtoId`, `tipo`, `page`, `limit` · **200** (paginado)

---

### 5.7 Pedidos — fluxo crítico

#### `POST /pedidos` — Cria um pedido e reserva o estoque (UC04)
**Auth:** CLIENTE (canais APP, WEB, TOTEM, PICKUP) · ATENDENTE (canal BALCAO, na própria unidade)

**Request**
```json
{
  "unidadeId": 1,
  "canalPedido": "TOTEM",
  "itens": [
    { "produtoId": 10, "quantidade": 2 },
    { "produtoId": 21, "quantidade": 1 }
  ],
  "clienteId": null,
  "formaPagamento": "MOCK"
}
```
| Campo | Regra |
|---|---|
| `unidadeId` | Obrigatório; unidade ativa |
| `canalPedido` | **Obrigatório**; APP, TOTEM, BALCAO, PICKUP ou WEB (RN01); compatível com o perfil (RN03) |
| `itens` | Obrigatório; 1 a 50 itens; produtos repetidos têm as quantidades somadas |
| `itens[].quantidade` | Inteiro de 1 a 99 |
| `clienteId` | Opcional e aceito **apenas** do ATENDENTE (cliente identificado no balcão). Para o CLIENTE, o valor é ignorado e vem do token (RN04) |
| `formaPagamento` | Opcional; único valor aceito: `MOCK` |
| Preço ou total no corpo | **Ignorados**: o total é sempre calculado pela API (RN05) |

**201**
```json
{
  "id": 42,
  "unidadeId": 1,
  "clienteId": 5,
  "canalPedido": "TOTEM",
  "status": "AGUARDANDO_PAGAMENTO",
  "itens": [
    { "produtoId": 10, "nome": "Tapioca de carne de sol", "quantidade": 2, "precoUnitario": 15.90, "subtotal": 31.80 },
    { "produtoId": 21, "nome": "Suco de cajá", "quantidade": 1, "precoUnitario": 7.50, "subtotal": 7.50 }
  ],
  "total": 39.30,
  "criadoEm": "2026-12-03T14:20:00Z",
  "atualizadoEm": "2026-12-03T14:20:00Z"
}
```
**Erros**

| HTTP | `error` | Teste |
|---|---|---|
| 401 | `NAO_AUTENTICADO` | |
| 403 | `ACESSO_NEGADO` (ex.: COZINHA; ATENDENTE de outra unidade) | |
| 404 | `UNIDADE_NAO_ENCONTRADA` / `PRODUTO_NAO_ENCONTRADO` | T07 |
| 409 | `ESTOQUE_INSUFICIENTE`, com `details` por item | T08 |
| 422 | `VALIDACAO` (canal ausente ou inválido, quantidade ≤ 0, lista vazia) | T04, T05 |
| 422 | `CANAL_INVALIDO_PARA_PERFIL` | |

Exemplo de `409` (T08):
```json
{
  "error": "ESTOQUE_INSUFICIENTE",
  "message": "Não há quantidade suficiente para um ou mais itens.",
  "details": [ { "field": "itens[0].quantidade", "issue": "Produto 10 — solicitado: 5, disponível: 1" } ],
  "timestamp": "2026-12-03T14:20:00Z",
  "path": "/pedidos",
  "requestId": "…"
}
```

#### `GET /pedidos` — Lista pedidos com filtros
**Auth:** todos os perfis, com **escopo automático**:

| Perfil | Vê |
|---|---|
| CLIENTE | Apenas os próprios pedidos |
| ATENDENTE, COZINHA, GERENTE | Pedidos da própria unidade |
| ADMIN | Todos (pode filtrar por `unidadeId`) |

**Query:** `canalPedido`, `status`, `unidadeId` (ADMIN), `dataInicio`, `dataFim` (ISO 8601), `page`, `limit`. Ordenação: mais recentes primeiro.

Exemplo: `GET /pedidos?canalPedido=TOTEM&status=AGUARDANDO_PAGAMENTO&page=1&limit=10`

**200** (paginado; itens resumidos)
```json
{
  "items": [
    { "id": 42, "unidadeId": 1, "canalPedido": "TOTEM", "status": "AGUARDANDO_PAGAMENTO", "total": 39.30, "quantidadeItens": 3, "criadoEm": "2026-12-03T14:20:00Z" }
  ],
  "page": 1, "limit": 10, "totalItems": 1, "totalPages": 1
}
```
**Erros:** `401` (T02) · `422` (canal ou status fora do enum; página inválida)

> Fila da cozinha: `GET /pedidos?status=PAGO` e `GET /pedidos?status=EM_PREPARO`.

#### `GET /pedidos/{id}` — Detalha um pedido
**200**: mesmo formato da resposta de criação · **Erros:** `401` · `403` (pedido de outro cliente ou de outra unidade) · `404 PEDIDO_NAO_ENCONTRADO`

#### `PATCH /pedidos/{id}/status` — Avança o status do pedido
**Auth:** conforme a máquina de estados (RN11)

| De → Para | Perfil |
|---|---|
| `PAGO → EM_PREPARO` | COZINHA |
| `EM_PREPARO → PRONTO` | COZINHA |
| `PRONTO → ENTREGUE` | ATENDENTE |

**Request**
```json
{ "status": "EM_PREPARO" }
```
Não aceita `PAGO` (só via pagamento) nem `CANCELADO` (só via cancelamento): ambos → `409 TRANSICAO_INVALIDA`. Gera auditoria `STATUS_ALTERADO` com o status anterior e o novo.

**200**: o pedido atualizado
**Erros:** `401` · `403` (perfil não autorizado para essa transição, ou outra unidade) · `404` · `409 TRANSICAO_INVALIDA` (T12) · `422` (status fora do enum)

#### `POST /pedidos/{id}/cancelamentos` — Cancela o pedido e devolve o estoque
**Auth:** conforme RN11

| Status atual | Quem pode cancelar |
|---|---|
| `AGUARDANDO_PAGAMENTO` | CLIENTE (dono), ATENDENTE, GERENTE |
| `PAGO` | Somente GERENTE (o estorno do pagamento é apenas documentado) |
| Demais | Ninguém → `409 PEDIDO_NAO_CANCELAVEL` |

**Request**
```json
{ "motivo": "Cliente desistiu" }
```
**200**: pedido com `status: CANCELADO`. Na mesma transação, o estoque reservado é devolvido (`ESTORNO_RESERVA`) e a auditoria `PEDIDO_CANCELADO` é gravada.
**Erros:** `401` · `403` · `404` · `409 PEDIDO_NAO_CANCELAVEL` · `422` (motivo ausente)

#### `GET /pedidos/{id}/pagamentos` — Tentativas de pagamento do pedido
**200**: lista de pagamentos (formato de 5.8) · **Erros:** `401` · `403` · `404`

---

### 5.8 Pagamentos — fluxo crítico

#### `POST /pagamentos` — Solicita o pagamento ao gateway mock (UC05)
**Auth:** CLIENTE (dono do pedido) · ATENDENTE (unidade do pedido)
**Cabeçalho obrigatório:** `Idempotency-Key: 3f8a1c52-9d4e-4b7a-8c21-6e5f0a9b7d13`

**Request**
```json
{ "pedidoId": 42, "tokenPagamento": "tok_aprovado" }
```
| `tokenPagamento` | Resultado do mock (RN09) |
|---|---|
| `tok_aprovado` | APROVADO |
| `tok_recusado` | RECUSADO (motivo: "Saldo insuficiente") |
| `tok_timeout` | Falha do gateway → 502 |
| Qualquer outro valor | RECUSADO (motivo: "Token de pagamento inválido") |

O valor cobrado é sempre o `total` do pedido (RN10).

**201 — aprovado** (T09)
```json
{
  "id": 7,
  "pedidoId": 42,
  "status": "APROVADO",
  "valor": 39.30,
  "gatewayTransacaoId": "mock_9f2c7a1e",
  "motivoRecusa": null,
  "statusPedido": "PAGO",
  "mensagem": "Pagamento aprovado.",
  "criadoEm": "2026-12-03T14:21:00Z"
}
```
**201 — recusado** (T10)
```json
{
  "id": 8,
  "pedidoId": 43,
  "status": "RECUSADO",
  "valor": 18.00,
  "gatewayTransacaoId": "mock_1b7e4d90",
  "motivoRecusa": "Saldo insuficiente",
  "statusPedido": "AGUARDANDO_PAGAMENTO",
  "tentativasRestantes": 2,
  "mensagem": "Pagamento recusado: saldo insuficiente. Você pode tentar novamente.",
  "criadoEm": "2026-12-03T14:22:00Z"
}
```
Na **3ª recusa**: `statusPedido: "CANCELADO"`, `tentativasRestantes: 0` e a mensagem *"Pagamento recusado. Limite de tentativas atingido; o pedido foi cancelado."*

> **Por que 201 também na recusa?** A requisição foi processada com sucesso: a tentativa de pagamento foi **criada e registrada**. O resultado de negócio (aprovado ou recusado) vem no campo `status`. É o mesmo comportamento dos gateways reais.

**200 — repetição idempotente:** a mesma `Idempotency-Key` com o mesmo `pedidoId`, já com resultado final, devolve o pagamento registrado **sem chamar o gateway de novo** (RN08).

**Erros**

| HTTP | `error` | Situação |
|---|---|---|
| 401 | `NAO_AUTENTICADO` | |
| 403 | `ACESSO_NEGADO` | Pedido de outro cliente ou de outra unidade |
| 404 | `PEDIDO_NAO_ENCONTRADO` | |
| 409 | `PEDIDO_NAO_AGUARDA_PAGAMENTO` | Pedido já pago, cancelado ou em outro status |
| 409 | `IDEMPOTENCY_KEY_CONFLITO` | Chave já usada para **outro** pedido |
| 422 | `VALIDACAO` | `pedidoId`, `tokenPagamento` ou o cabeçalho `Idempotency-Key` ausentes |
| 502 | `GATEWAY_INDISPONIVEL` | `tok_timeout`. O pagamento fica `ERRO`, o pedido não muda, e o cliente pode repetir com a **mesma** chave |

#### `GET /pagamentos/{id}` — Consulta um pagamento
**200**: formato acima (sem `mensagem` e `tentativasRestantes`) · **Erros:** `401` · `403` · `404`

> Os payloads enviados e recebidos do gateway ficam gravados no banco para auditoria, mas **não** são expostos ao cliente.

---

### 5.9 Fidelidade (simplificada)

Regras: **1 ponto por R$ 1,00** do total do pedido (arredondado para baixo), creditado quando o pedido vira `PAGO`, apenas para clientes com consentimento `FIDELIDADE` ativo (RN13). Todos os endpoints exigem consentimento ativo; sem ele → `403 CONSENTIMENTO_NECESSARIO`.

#### `GET /fidelidade/saldo`
**Auth:** CLIENTE · **200**
```json
{ "saldo": 240, "consentimentoAtivo": true }
```

#### `GET /fidelidade/extrato`
**Auth:** CLIENTE · **Query:** `page`, `limit` · **200** (paginado)
```json
{
  "items": [
    { "id": 31, "tipo": "CREDITO", "pontos": 39, "pedidoId": 42, "criadoEm": "2026-12-03T14:21:00Z" },
    { "id": 35, "tipo": "RESGATE", "pontos": -100, "pedidoId": null, "criadoEm": "2026-12-04T09:00:00Z" }
  ],
  "page": 1, "limit": 10, "totalItems": 2, "totalPages": 1
}
```

#### `POST /fidelidade/resgates`
**Auth:** CLIENTE

**Request**
```json
{ "pontos": 100 }
```
Regras: múltiplos de 100; no máximo o saldo disponível.
**201**
```json
{ "id": 35, "pontos": 100, "saldoRestante": 140, "criadoEm": "2026-12-04T09:00:00Z" }
```
**Erros:** `401` · `403 CONSENTIMENTO_NECESSARIO` · `409 PONTOS_INSUFICIENTES` · `422` (não é múltiplo de 100)

> **Simplificação declarada:** no MVP, o resgate debita os pontos e fica registrado no extrato. A **aplicação do benefício** (desconto no pedido, brinde, descontos progressivos e campanhas segmentadas) fica **documentada como proposta**.

---

### 5.10 Auditoria

#### `GET /auditoria` — Consulta registros de ações sensíveis
**Auth:** GERENTE, ADMIN · **Query:** `entidade` (ex.: `pedido`), `entidadeId`, `acao`, `usuarioId`, `dataInicio`, `dataFim`, `page`, `limit`

**200** (paginado)
```json
{
  "items": [
    {
      "id": 501,
      "usuarioId": 5,
      "acao": "PEDIDO_CRIADO",
      "entidade": "pedido",
      "entidadeId": 42,
      "dadosAntes": null,
      "dadosDepois": { "status": "AGUARDANDO_PAGAMENTO", "total": 39.30, "canalPedido": "TOTEM" },
      "requestId": "7f3c2a9e-…",
      "criadoEm": "2026-12-03T14:20:00Z"
    }
  ],
  "page": 1, "limit": 10, "totalItems": 1, "totalPages": 1
}
```
**Ações registradas:** `PEDIDO_CRIADO`, `STATUS_ALTERADO`, `PEDIDO_CANCELADO`, `PAGAMENTO_APROVADO`, `PAGAMENTO_RECUSADO`, `PAGAMENTO_ERRO`, `ESTOQUE_MOVIMENTADO`, `CONSENTIMENTO_CONCEDIDO`, `CONSENTIMENTO_REVOGADO`.

Dados pessoais aparecem **mascarados** nos registros (ex.: `m***@exemplo.com`).

**Erros:** `401` · `403` (T03 alternativo: CLIENTE)

> Melhoria documentada: restringir o GERENTE aos registros da própria unidade.

---

## 6. Rastreabilidade com o plano de testes

| ID | Cenário | Endpoint | Esperado | Tipo |
|---|---|---|---|---|
| T01 | Login válido | `POST /auth/login` | 200 + `accessToken` | Positivo |
| T02 | Acesso sem token | `GET /pedidos` | 401 `NAO_AUTENTICADO` | Negativo |
| T03 | Perfil sem permissão | `POST /estoque/movimentacoes` como CLIENTE | 403 `ACESSO_NEGADO` | Negativo |
| T04 | `canalPedido` ausente | `POST /pedidos` | 422 `VALIDACAO` com `details[0].field = "canalPedido"` | Negativo |
| T05 | Formato inválido | `POST /pedidos` (quantidade −1) e `POST /usuarios` (e-mail inválido) | 422 `VALIDACAO` | Negativo |
| T06 | Pedido válido | `POST /pedidos` | 201 + `AGUARDANDO_PAGAMENTO` + `total` calculado | Positivo |
| T07 | Produto inexistente | `POST /pedidos` com `produtoId: 9999` | 404 `PRODUTO_NAO_ENCONTRADO` | Negativo |
| T08 | Estoque insuficiente | `POST /pedidos` com quantidade acima do saldo | 409 `ESTOQUE_INSUFICIENTE` | Negativo |
| T09 | Pagamento aprovado | `POST /pagamentos` com `tok_aprovado` | 201 + `status: APROVADO` + `statusPedido: PAGO` | Positivo |
| T10 | Pagamento recusado | `POST /pagamentos` com `tok_recusado` | 201 + `status: RECUSADO` + mensagem | Positivo |
| T11 | Filtro por canal | `GET /pedidos?canalPedido=TOTEM` | 200 + apenas pedidos TOTEM | Positivo |
| T12 | Transição inválida | `PATCH /pedidos/{id}/status` (`AGUARDANDO_PAGAMENTO → PRONTO`) | 409 `TRANSICAO_INVALIDA` | Negativo |
| T13 | Auditoria | `GET /auditoria?entidade=pedido&entidadeId={id}` | 200 + registros `PEDIDO_CRIADO` e `STATUS_ALTERADO` | Positivo |
| T14 | Idempotência | `POST /pagamentos` repetido com a mesma chave | 200 + mesmo pagamento, sem nova cobrança | Positivo (extra) |
| T15 | Gateway indisponível | `POST /pagamentos` com `tok_timeout` | 502 `GATEWAY_INDISPONIVEL`; pedido continua aguardando | Negativo (extra) |
| T16 | Fidelidade sem consentimento | `GET /fidelidade/saldo` sem consentimento | 403 `CONSENTIMENTO_NECESSARIO` | Negativo (extra) |
| T17 | Cancelamento devolve estoque | `POST /pedidos/{id}/cancelamentos` + `GET /estoque` | 200 `CANCELADO` + saldo restaurado | Positivo (extra) |

Total: **8 positivos e 9 negativos**, acima do mínimo do roteiro (6 positivos e 4 negativos).

---

## 7. Fora do MVP (documentado como proposta)

| Item | Motivo |
|---|---|
| `POST /auth/refresh` e `POST /auth/logout` | Exigem armazenamento de tokens de atualização ou lista de bloqueio |
| Estorno de pagamento ao cancelar pedido `PAGO` | Depende de integração real com o gateway |
| Aplicação do resgate de pontos como desconto | Descontos progressivos e campanhas são propostas (RF24) |
| `/promocoes` e `/campanhas` | RF24: regras descritas no PDF |
| `/relatorios` da matriz (vendas por unidade e região) | RF26 |
| Versionamento `/v1` | Desnecessário enquanto há um único consumidor; seria adotado antes da primeira mudança incompatível |
| Rate limiting no login | Proteção contra força bruta; proposta para o API Gateway |
