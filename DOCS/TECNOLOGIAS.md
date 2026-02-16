# Visão Geral das Tecnologias e Frameworks

Este documento apresenta, de forma didática, as principais tecnologias, bibliotecas e componentes utilizados no Equivalence Engine Service. O objetivo é ajudar novos colaboradores a entender por que cada peça existe, onde procurar o código relacionado e quando ajustar cada configuração.

**Como ler este documento:** cada seção traz uma breve descrição, por que usamos a tecnologia aqui, onde o código/configuração relevante está no repo e links rápidos para arquivos importantes.

---

## Docker & Orquestração

- **O que é:** Contêineres para empacotar serviços e `docker compose` para orquestração local.
- **Por que usamos:** Facilita levantar todo o ambiente (Postgres, Redis, web, worker, mocks) com uma única configuração reproduzível.
- **Onde:** `docker-compose.yml` na raiz contém todos os serviços.
- **Serviços:** `web`, `worker`, `mock-embed`, `mock-llm`, `redis`, `postgres`.

---

## Python (3.10+)

- **O que é:** Linguagem principal do projeto.
- **Por que usamos:** Ecossistema rico (FastAPI, SQLAlchemy, RQ) e facilidades de desenvolvimento.
- **Onde:** `app/` contém toda a lógica da aplicação.

---

## FastAPI + Uvicorn

- **O que é:** `FastAPI` é um framework web moderno para construir APIs; `uvicorn` é o servidor ASGI.
- **Por que usamos:** performance, tipagem, documentação automática (OpenAPI) e desenvolvimento ágil.
- **Onde:** `app/main.py`, `app/asgi.py` — entrypoints; `app/api/` — rotas e schemas.

---

## PostgreSQL

- **O que é:** Banco de dados relacional usado para persistência (tenants, api_keys, auditoria, taxonomias).
- **Por que usamos:** transações, consistência e suporte a SQL/ACID.
- **Onde:** serviço `postgres` no Compose; migrações em `alembic/`; modelos em `app/models.py`.

---

## Redis

- **O que é:** Armazenamento em memória usado como fila (RQ) e cache.
- **Por que usamos:** RQ (Redis Queue) para processamento assíncrono de jobs batch; cache de embeddings (opcional).
- **Onde:** `app/redis_client.py`, `app/queue.py`; worker em `app/worker.py`.

---

## RQ (Redis Queue)

- **O que é:** Biblioteca de filas baseada em Redis para jobs assíncronos.
- **Por que usamos:** processamento em lote de avaliações sem bloquear a API.
- **Onde:** `app/queue.py`, `app/worker.py`, `app/rq_hooks.py`; jobs batch em `app/api/batch_routes.py`.

---

## SQLAlchemy + Alembic

- **SQLAlchemy:** ORM usado para modelos e acesso a dados.
- **Alembic:** migrações de schema.
- **Onde:** `app/db.py`, `app/models.py`; migrações em `alembic/versions/`.

---

## Pydantic

- **O que é:** Validação de dados e schemas para APIs.
- **Por que usamos:** integração nativa com FastAPI, validação automática de payloads.
- **Onde:** `app/api/schemas.py` — `EvaluateRequest`, `EvaluateResponse`, etc.

---

## Mappers (Embeddings + LLM)

- **O que é:** Componentes que mapeiam texto (ementas) para categorias da taxonomia usando embeddings e/ou LLM.
- **Por que usamos:** permitir decisões semânticas e explicáveis sobre equivalência de disciplinas.
- **Onde:** `app/mapper/` — `stub_mapper.py`, `embedding_llm_mapper.py`, `fallback_mapper.py`; clientes em `app/mapper/clients.py`.
- **Configuração:** `EMBED_URL`, `EMBED_API_KEY`, `LLM_URL`, `LLM_API_KEY` no `.env`.

---

## Engine (Motor de Decisão)

- **O que é:** Núcleo que aplica regras hard-coded, scoring e gera justificativas.
- **Por que usamos:** decisões determinísticas, auditáveis e explicáveis.
- **Onde:** `app/engine/` — `service.py`, `hard_rules.py`, `scoring.py`, `decision.py`, `justification.py`.

---

## prometheus_client

- **O que é:** Exposição de métricas no formato Prometheus.
- **Por que usamos:** observabilidade (latência, contadores, erros).
- **Onde:** `app/metrics.py`; endpoint `/metrics` exposto pela aplicação.

---

## Estrutura do Repositório (alto nível)

- `app/` — código da aplicação
  - `api/` — rotas, schemas, batch
  - `engine/` — motor de decisão
  - `mapper/` — mappers (embeddings, LLM)
  - `tools/` — stubs (embed_stub, etc.)
- `alembic/` — migrações
- `scripts/` — utilitários (seed, sweep, check_keys)
- `tests/` — testes unitários
- `DOCS/` — documentação principal
- `docs/` — documentação operacional

---

## Problemas comuns e onde olhar

- **Worker não processa jobs:** verificar Redis (`redis-cli ping`), fila RQ (`rq info`), logs do worker.
- **Erro de conexão DB:** verificar `DATABASE_URL` e se Postgres está up.
- **Mapper externo não responde:** testar `EMBED_URL`/`LLM_URL` com `curl`; usar fallback mapper.
- **Migrations falharam:** verificar `alembic_version` e estado das tabelas.
- **API retorna 401:** verificar `X-API-Key` e se a chave existe no banco (hash correto com `API_KEY_SALT`).
