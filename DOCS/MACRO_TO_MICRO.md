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

1. Cliente envia requisição ao endpoint (ex.: `POST /v1/evaluate`). Veja rotas em [app/api/routes.py](app/api/routes.py) e [app/api/batch_routes.py](app/api/batch_routes.py).
2. A rota valida payload com `pydantic` (esquemas em [app/api/schemas.py](app/api/schemas.py)).
3. A requisição é encaminhada ao serviço de execução/engine: [app/engine/service.py](app/engine/service.py).
4. O `service` orquestra mapeadores (`app/mapper/*`), validações (`app/engine/validator.py`) e regras (`app/engine/hard_rules.py`).
5. Se necessário, tarefas são enfileiradas via [app/queue.py](app/queue.py) / `rq` e processadas por [app/worker.py](app/worker.py).
6. Resultados (decisões, justificativas) são salvos/consultados via [app/db.py](app/db.py) e repositórios em [app/repos.py](app/repos.py) e [app/audit](app/audit/).
7. Serviços auxiliares: cache ([app/cache/cache.py](app/cache/cache.py)), taxonomia ([app/taxonomy/store.py](app/taxonomy/store.py)), embeddings/index ([app/index_builder.py]).

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
      - '5432:5432'

  redis:
    image: redis:7
    ports:
      - '6379:6379'

  web:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./:/usr/src/app:ro
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/equivalence
      REDIS_URL: redis://redis:6379/0
    ports:
      - '8000:8000'
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