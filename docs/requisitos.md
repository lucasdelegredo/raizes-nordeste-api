# Análise e Requisitos — API Raízes do Nordeste

Versão 0.1 — 24/11/2026

## Legenda de prioridade

| Nível | Significado |
|---|---|
| **I — Implementado** | Código + teste na coleção. Faz parte do MVP. |
| **S — Simplificado** | Implementado em versão reduzida, com a limitação explicada. |
| **D — Documentado** | Proposta descrita no PDF, sem código. |

Critério de priorização: entra como **I** tudo o que é necessário para fechar o fluxo crítico (Pedido → Pagamento mock → Status) e o que o roteiro exige em qualquer fluxo (persistência, JWT com perfis, erro padronizado). Cai para **S** ou **D** o que agrega valor de negócio, mas não bloqueia o fluxo crítico.

## Requisitos Funcionais (RF)

| ID | Requisito | Prioridade | Justificativa |
|---|---|---|---|
| RF01 | Cadastrar usuário (cliente) com nome, e-mail e senha | I | Necessário para pedidos identificados e fidelidade |
| RF02 | Autenticar usuário (login) e emitir token JWT | I | Exigência mínima do roteiro |
| RF03 | Controlar acesso por perfil: CLIENTE, ATENDENTE, COZINHA, GERENTE, ADMIN | I | Cada ator do caso de uso tem permissões próprias |
| RF04 | Listar e detalhar unidades da rede | I | Pedido é sempre vinculado a uma unidade |
| RF05 | Gerenciar unidades (criar/editar) | S | Só ADMIN; dados iniciais vêm do seed |
| RF06 | Manter catálogo de produtos (CRUD, consulta paginada) | I | Base do cardápio e do cálculo do total |
| RF07 | Consultar cardápio por unidade (produtos disponíveis naquele local) | I | Unidades têm cardápios diferentes (cozinha completa × reduzida) |
| RF08 | Registrar entrada e saída de estoque por unidade | I | Controle de estoque local |
| RF09 | Consultar saldo de estoque por unidade | I | Suporte ao gerente |
| RF10 | Bloquear venda de produto sem estoque suficiente | I | Regra do fluxo crítico (409 ESTOQUE_INSUFICIENTE) |
| RF11 | Criar pedido com itens, unidade e `canalPedido` obrigatório | I | Núcleo do fluxo crítico + multicanalidade |
| RF12 | Calcular o total do pedido no back-end a partir do preço do produto | I | Não confiar em valor enviado pelo cliente |
| RF13 | Listar pedidos com filtros `canalPedido` e `status`, com paginação | I | Rastreabilidade por canal |
| RF14 | Detalhar pedido | I | Acompanhamento de status pelo cliente |
| RF15 | Atualizar status do pedido conforme máquina de estados e perfil | I | AGUARDANDO_PAGAMENTO → PAGO → EM_PREPARO → PRONTO → ENTREGUE |
| RF16 | Cancelar pedido (somente em estados permitidos), devolvendo estoque | I | Operação sensível, auditada |
| RF17 | Solicitar pagamento a um gateway externo (mock) e registrar cada tentativa | I | Pagamento desacoplado; não processa pagamento real |
| RF18 | Atualizar o pedido conforme o retorno do pagamento (aprovado/recusado) | I | Fecha o fluxo crítico |
| RF19 | Registrar consentimento LGPD (finalidade, versão, data) | I | Fidelidade só com consentimento |
| RF20 | Acumular pontos por pedido pago | S | Regra fixa (ex.: 1 ponto por R$ 1); sem descontos progressivos |
| RF21 | Consultar saldo/histórico e resgatar pontos | S | Resgate simples, sem campanhas segmentadas |
| RF22 | Registrar auditoria de ações sensíveis | I | Criação/cancelamento de pedido, status, pagamento, estoque manual |
| RF23 | Consultar registros de auditoria | I | GERENTE/ADMIN |
| RF24 | Promoções e campanhas (regras de aplicação) | D | Não bloqueia o fluxo; descrito como proposta |
| RF25 | Produtos sazonais (ex.: período junino) | D | Proposta: janela de disponibilidade no cardápio |
| RF26 | Relatórios consolidados da matriz (vendas por unidade/região, mais vendidos) | D | Proposta: consultas agregadas / read model |

## Requisitos Não Funcionais (RNF)

| ID | Requisito | Prioridade | Como será atendido |
|---|---|---|---|
| RNF01 | Senhas armazenadas somente com hash | I | argon2 via pwdlib |
| RNF02 | Autenticação por token nas rotas protegidas | I | JWT (PyJWT), dependência `get_current_user` |
| RNF03 | Autorização por perfil | I | Dependência `require_roles(...)` |
| RNF04 | Nenhum dado sensível em responses | I | `response_model` com schemas de saída próprios |
| RNF05 | Padrão único de erro JSON em toda a API (inclusive 401, 403, 422) | I | Handlers globais em `api/errors.py` |
| RNF06 | Auditoria de ações sensíveis (quem, o quê, quando, antes/depois) | I | Tabela `auditoria` |
| RNF07 | LGPD: minimização, consentimento, mascaramento em logs | I | Coleta mínima; e-mail mascarado em logs |
| RNF08 | LGPD: retenção e anonimização | D | Política descrita no PDF |
| RNF09 | Integração de pagamento desacoplada | I | Interface `PaymentGateway` + implementação mock |
| RNF10 | Tolerância a falhas no pagamento (idempotência, timeout) | S | Chave de idempotência; simulação de falha no mock |
| RNF11 | Consistência transacional: pedido + estoque (tudo ou nada) | I | Transação única do SQLAlchemy |
| RNF12 | Documentação OpenAPI/Swagger com exemplos e status codes | I | Gerada pelo FastAPI em `/docs` |
| RNF13 | Reprodutibilidade do ambiente | I | docker-compose + README + `.env.example` + seed |
| RNF14 | Paginação em listagens | I | `?page=&limit=` |
| RNF15 | Desempenho e disponibilidade em horários de pico | D | Proposta: réplicas, cache, filas, circuit breaker |
| RNF16 | Escalabilidade para novas unidades | D | Proposta arquitetural no PDF |

## Rastreabilidade com o plano de testes

| Teste | Requisitos cobertos |
|---|---|
| T01 Login válido | RF02 |
| T02 Acesso sem token | RNF02, RNF05 |
| T03 Perfil sem permissão | RF03, RNF03 |
| T04 `canalPedido` ausente | RF11, RNF05 |
| T05 Formato inválido | RF01/RF11, RNF05 |
| T06 Pedido válido | RF11, RF12 |
| T07 Produto/unidade inexistente | RF11 |
| T08 Estoque insuficiente | RF10 |
| T09 Pagamento aprovado | RF17, RF18 |
| T10 Pagamento recusado | RF17, RF18 |
| T11 Filtro por canal | RF13 |
| T12 Transição inválida | RF15 |
| T13 Auditoria | RF22, RF23, RNF06 |

## Decisões em aberto (resolver na modelagem, 25–29/11)

- Quando baixar o estoque: na criação do pedido (reserva) ou na aprovação do pagamento?
- Regra determinística do pagamento mock (campo no request ou valor-gatilho?).
- Quais perfis podem cancelar e até qual status.
