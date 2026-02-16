# Macro → Micro: Guia didático do código

Objetivo: descrever, de forma clara e didática, a arquitetura do projeto do nível macro (visão geral/fluxos) ao micro (módulos e funções), explicando a função de cada componente e apontando onde buscar o código.

**Sumário**
- Visão geral (macro)
- Fluxo de requisição (macro → micro)
- Componentes principais (micro) — responsabilidade e arquivos
- Pontos de extensão e hooks
- Como navegar no código (mapa rápido)

## Visão geral (macro)

Este repositório implementa um microserviço independente para avaliação de equivalência. Na visão macro temos:

- Entrada API (requests HTTP) e endpoints públicos.
- Processamento síncrono/assíncrono (workers, filas, batch jobs).
- Persistência e índices (banco, índice de taxonomia/embedding).
- Camadas de mapeamento (mapear entrada → vetores → decisões).
- Observabilidade, rate limit e segurança.

Arquivos de referência (visão macro):
- [app/main.py](app/main.py) — inicialização da aplicação e registro de rotas.
- [app/asgi.py](app/asgi.py) — adaptador ASGI (se existir configuração especial de deploy).
- [README.full.md](README.full.md) — documentação completa (macro → micro).

## Fluxo de requisição (macro → micro)

Abaixo cada etapa do fluxo com sua finalidade e um pequeno exemplo demonstrando o que entra/saí e por que a etapa existe.

1) Recepção do pedido (HTTP)
  - Finalidade: receber a requisição do cliente e expor o contrato (endpoint). Atua como porta de entrada do sistema.
  - Onde: [app/api/routes.py](app/api/routes.py), [app/api/batch_routes.py](app/api/batch_routes.py)
  - Exemplo: `POST /v1/equivalences/evaluate` com payload JSON (ver seção de exemplos no documento).

2) Validação / Parsing
  - Finalidade: garantir que o payload esteja completo e no formato esperado antes de processar (falha rápida para input inválido).
  - Onde: `pydantic` schemas em [app/api/schemas.py](app/api/schemas.py)
  - Exemplo: `pydantic` rejeita requests sem `origem.ementa` ou com `policy` faltando campos obrigatórios.

3) Orquestração pelo Engine (`service`)
  - Finalidade: núcleo que comanda o processamento — aplica regras, solicita mapeamento, calcula scores, decide e gera justificativas.
  - Onde: [app/engine/service.py](app/engine/service.py)
  - Exemplo: `service.evaluate(req)` segue passos internos (hard rules → mapping → scoring → decision → justification).

4) Regras determinísticas (Hard Rules)
  - Finalidade: executar checagens rápidas e determinísticas que podem encerrar o fluxo (p.ex. regras de elegibilidade, validade de carga horária, bloqueios administrativos).
  - Onde: [app/engine/hard_rules.py](app/engine/hard_rules.py)
  - Exemplo: se origem e destino tiverem o mesmo código curricular, retornar indeferido sem chamar mapeadores mais custosos.

5) Mapeamento (Text → Conceitos)
  - Finalidade: transformar texto (ementa) em conceitos/tokens da taxonomia (vetores/itens com confiança). É a etapa que chama LLMs/embeddings ou mapeadores locais.
  - Onde: `app/mapper/*` (ex.: `app/mapper/openai_mapper.py`, `app/mapper/embedding_llm_mapper.py`)
  - Exemplo: converter a ementa em uma lista de `MappedConcept(node_id, weight, confidence, evidence)`.

6) Scoring e cobertura
  - Finalidade: comparar vetores de origem/destino, calcular cobertura geral e crítica, aplicar penalidades por níveis e consolidar em um `score` final.
  - Onde: [app/engine/scoring.py](app/engine/scoring.py)
  - Exemplo: `coverage(vec_o, vec_d)` retorna conceitos cobertos e faltantes; `final_score(...)` converte métricas em valor numérico.

7) Decisão e justificativa
  - Finalidade: aplicar a política (`policy`) para transformar o `score` em uma decisão (`ACEITO` / `INDEFERIDO` / `REVISAR`) e gerar justificativas legíveis para auditoria e usuário.
  - Onde: [app/engine/decision.py](app/engine/decision.py), [app/engine/justification.py](app/engine/justification.py)
  - Exemplo: `decide(policy, score, cov_crit)` → `("ACEITO", "score acima do limiar")`, e `build_justification(...)` cria texto curto/detalhado.

8) Enfileiramento / Processamento Assíncrono
  - Finalidade: quando for batch ou processamento pesado, enfileirar jobs para workers; permite escalabilidade e desacoplamento.
  - Onde: [app/queue.py](app/queue.py), `rq` e [app/worker.py](app/worker.py)
  - Exemplo: `POST /v1/equivalences/batch` cria job em Redis via RQ; `worker` processa e grava resultado no DB.

9) Persistência, cache e auditoria
  - Finalidade: salvar decisões, justificativas e metas de execução; usar cache para acelerar mapeamentos e consultas; auditar requests para conformidade.
  - Onde: [app/db.py](app/db.py), [app/repos.py](app/repos.py), [app/cache/cache.py](app/cache/cache.py), [app/audit](app/audit/)
  - Exemplo: gravar `EvaluateResponse` em repositório e salvar hash das ementas para rastreabilidade.

Exemplo completo (fluxo simplificado):

1. Cliente envia `POST /v1/evaluate` com payload (ementas, policy, options).
2. `routes.py` valida via `pydantic` e chama `service.evaluate(req)`.
3. `service` aplica hard rules — se bloqueado, retorna `INDEFERIDO`.
4. Caso contrário, `service` pede ao `mapper` os conceitos mapeados (cache first).
5. `scoring` compara vetores e gera `score` e `breakdown`.
6. `decision` aplica política e gera `decisao` + `motivo`.
7. `justification` monta explicações; `audit` grava o resultado; resposta é retornada ao cliente.

Links rápidos: ver handlers em [app/api/routes.py](app/api/routes.py) e a implementação do orchestrador em [app/engine/service.py](app/engine/service.py).

## Componentes principais (micro) — responsabilidade e onde olhar

- `app/api/` — camada HTTP
  - `routes.py` e `batch_routes.py`: definem endpoints públicos e handlers.
  - `schemas.py`: modelos `pydantic` para validação de entrada/saída.

- `app/engine/` — núcleo de negócio
  - `service.py`: orquestrador principal; recebe entrada validada e comanda o processo.
  - `decision.py`: contém lógica que transforma scores em decisões (aceitar, rejeitar, revisar).
  - `scoring.py`: funções que calculam pontuações entre itens (ex.: similaridade).
  - `justification.py`: constrói justificativas legíveis para a decisão.
  - `hard_rules.py`: regras determinísticas (ex.: se curso X é igual a Y então aceitar).
  - `validator.py`: validações adicionais de domínio.

- `app/mapper/` — mapeamento e integração com LLM/embeddings
  - `embedding_llm_mapper.py`, `openai_mapper.py`, `fallback_mapper.py`: adaptadores que convertem texto em embeddings ou chamadas a LLMs.
  - `base.py`: contrato comum dos mapeadores.

- `app/index_builder.py` e `app/taxonomy/` — indexação e taxonomia
  - constroem e consultam índices de busca e o grafo/estrutura de taxonomia.
  - importantes para recuperar correspondências e relacionamentos semânticos.

- `app/repos.py`, `app/db.py`, `app/cache/cache.py` — persistência
  - `db.py`: inicialização de conexão e sessões DB.
  - `repos.py`: camadas de repositório (CRUD) usadas pelo `service`.
  - `cache/cache.py`: cache de respostas/consultas para performance.

- `app/worker.py`, `app/queue.py`, `rq_hooks.py` — processamento assíncrono
  - gerenciam jobs em fila (`rq`) para processamento em background (batchs, recalculo, indexação).

- `app/security.py`, `app/rate_limiter.py`, `app/middlewares.py` — infra
  - autenticação, autorização, limites e middlewares de observabilidade.

- `app/tuning.py`, `app/seed.py`, `tune_cli.py` — ferramentas operacionais
  - scripts e comandos para tune, carga inicial e ajustes.

## Sequência típica (mais detalhada)

- Sync request (rápida): route → schemas → service.process_sync()
  - `service` chama `mapper` → `scoring` → `decision` → `justification` → retorna JSON.

- Async / Batch: route → enfileira job via `queue` → `worker` processa (reusa `service`) → escreve resultado no DB / envia callback.

Arquivos exemplos:
- Fluxo de requisição: [app/api/routes.py](app/api/routes.py)
- Serviço orquestrador: [app/engine/service.py](app/engine/service.py)
- Worker: [app/worker.py](app/worker.py)

## Pontos de extensão e onde alterar

- Para trocar provedor de embeddings/LLM: implementar ou modificar `app/mapper/openai_mapper.py` ou adicionar novo mapper seguindo `app/mapper/base.py`.
- Para alterar regras de decisão: editar `app/engine/hard_rules.py` e `app/engine/decision.py`.
- Para mudar persistência: adaptar `app/repos.py` e `app/db.py`.
- Para adicionar novas rotas/funcionalidades: criar handlers em `app/api/routes.py` e adicionar esquemas em `app/api/schemas.py`.

## Dicas para leitura do código (mapa rápido)

- Comece por `app/main.py` para ver a configuração global (middlewares, dependências).
- Abra um endpoint em `app/api/routes.py` e siga até `service.py` para ver o fluxo de execução.
- Revise `app/engine/scoring.py` e `app/engine/decision.py` para entender como as decisões são tomadas.
- Se o comportamento estiver falhando em produção, verifique `app/worker.py`, logs e `rq_hooks.py`.

## Referências rápidas (arquivos principais)
- [app/main.py](app/main.py)
- [app/api/routes.py](app/api/routes.py)
- [app/api/schemas.py](app/api/schemas.py)
- [app/engine/service.py](app/engine/service.py)
- [app/engine/decision.py](app/engine/decision.py)
- [app/engine/scoring.py](app/engine/scoring.py)
- [app/mapper/base.py](app/mapper/base.py)
- [app/mapper/openai_mapper.py](app/mapper/openai_mapper.py)
- [app/index_builder.py](app/index_builder.py)
- [app/db.py](app/db.py)
- [app/repos.py](app/repos.py)
- [app/worker.py](app/worker.py)
- [README.full.md](README.full.md)

---

## Frameworks e bibliotecas principais

Lista das dependências e frameworks usados no projeto com uma breve explicação da finalidade de cada um:

- **FastAPI**: framework web assíncrono usado para expor a API HTTP e definir rotas e dependências (`app/main.py`, `app/api/`).
- **Uvicorn / Gunicorn**: servidores ASGI/WGI para executar a aplicação em produção ou desenvolvimento (`uvicorn` usado no desenvolvimento, `gunicorn` em deploy com workers).
- **Pydantic**: validação e modelagem de dados (request/response schemas) usada em `app/api/schemas.py`.
- **SQLAlchemy**: ORM e camada de acesso a banco de dados (modelos e sessão DB em `app/db.py`, `app/repos.py`).
- **psycopg2-binary**: driver PostgreSQL síncrono (usado quando necessário para conexões sync).
- **asyncpg**: driver PostgreSQL assíncrono (usado para operações async performáticas).
- **Alembic**: ferramenta de migrações de esquema do banco; mantém versões de schema (`alembic/`).
- **Redis**: armazenamento em memória usado como broker/cache (cache local/internacionalização, filas, rate-limiting). Veja `app/redis_client.py` e uso em `app/cache`.
- **RQ**: fila de jobs (Redis Queue) usada para processamento assíncrono/background (`app/queue.py`, `app/worker.py`, `rq_hooks.py`).
- **httpx / requests**: clientes HTTP para chamadas externas (integração com serviços externos, mapeadores, webhooks).
- **numpy**: operações numéricas/arrays (usado nas rotinas de scoring e vetorização se necessário).
- **jinja2**: template engine (templates HTML em `templates/`, usado para dashboards/relatórios).
- **python-multipart**: suporte a multipart/form-data uploads (se endpoints aceitarem arquivos).
- **python-dotenv**: carregamento de variáveis de ambiente a partir de `.env` em ambientes de desenvolvimento.
- **pytest**: suíte de testes e runner (usado em `tests/`).

Observações operacionais:
- **Redis + RQ**: Redis atua como broker para `RQ` e também pode ser usado como cache; garanta que o serviço Redis esteja disponível para executar workers.
- **Alembic**: rode `alembic upgrade head` ao implantar mudanças no schema.
- **Drivers DB**: `asyncpg` é recomendado para endpoints/fluxos async; `psycopg2-binary` é útil para ferramentas de manutenção sync (migrations, scripts).

Abaixo há um exemplo prático de `docker-compose.yml` para subir Postgres + Redis + web (Uvicorn) + worker (RQ). Ajuste conforme seu ambiente.

```yaml
version: '3.8'
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: equivalence
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - '5433:5432'

  redis:
    image: redis:7
    ports:
      - '6380:6379'

  web:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./:/usr/src/app:ro
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/equivalence
      REDIS_URL: redis://redis:6379/0
    ports:
      - '8100:8000'
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: rq worker -u redis://redis:6379/0 default
    volumes:
      - ./:/usr/src/app:ro
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/equivalence
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis
      - db

volumes:
  postgres_data:
```

Comandos úteis:

```bash
# subir DB e Redis
docker-compose up -d db redis

# aplicar migrações Alembic (dentro do serviço web)
docker-compose run --rm web alembic upgrade head

# subir web e worker
docker-compose up -d web worker
```

Notas:
- Use `env_file:` para carregar variáveis sensíveis (não as commit no repo).
- O `build: .` assume que existe um `Dockerfile` na raiz (há um `Dockerfile` neste repositório). Ajuste se preferir usar uma imagem pré-builtin.

Se quiser, eu commito esta alteração e dou push para `main`.

<!-- merged EXTRA -->

Diagrama ASCII (fluxo simplificado)

Cliente -> HTTP Endpoint -> `app/api/routes.py`
                             |
                             v
                       Validação (`pydantic`)
                             |
                             v
                    `app/engine/service.py` (orquestrador)
                             |
         +-------------------+-------------------+
         |                   |                   |
         v                   v                   v
    `mapper`            `scoring`            `decision`/
  (`app/mapper`)     (`app/engine/scoring.py`) `app/engine/decision.py`
         |                   |                   |
         +-------------------+-------------------+
                             |
                             v
                        Justificação
                        (`app/engine/justification.py`)
                             |
                             v
                        Persistência / Audit
                        (`app/repos.py`, `app/audit`)

Exemplos de payloads

Requisição (exemplo simplificado):

```json
{
  "request_id": "req-123",
  "origem": {
    "ementa": "Introdução a programação: variáveis, controle de fluxo",
    "carga_horaria": 60
  },
  "destino": {
    "ementa": "Fundamentos de programação: tipos, estruturas de controle",
    "carga_horaria": 60
  },
  "policy": {
    "confidence_cutoff": 0.3
  },
  "options": {
    "allow_degraded_fallback": true,
    "return_evidence": true
  }
}
```

Resposta (exemplo simplificado):

```json
{
  "request_id": "req-123",
  "decisao": "ACEITO",
  "score": 0.87,
  "breakdown": {"cobertura": 0.9, "cobertura_critica": 0.85, "penalidade_nivel": 0.05},
  "justificativa_curta": "Ocorrências suficientes...",
  "justificativa_detalhada": "Explicação passo a passo...",
  "evidence": {"covered_concepts": [], "missing_concepts": []},
  "degraded_mode": false
}
```

Notas rápidas:
- Use `options.allow_degraded_fallback` quando quiser tentar um mapper alternativo (mais genérico) ao primário.
- `policy.confidence_cutoff` controla o que é considerado "confiável" no mapeamento para cálculo de cobertura.

