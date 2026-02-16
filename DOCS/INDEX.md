# Índice do Repositório

Este arquivo descreve os principais documentos e arquivos do projeto, com uma breve explicação do propósito de cada um.

Documentação (arquivos que eu adicionei):

- `README.md`: guia principal (resumo + link para o guia completo). Contém instruções rápidas para rodar, exemplos e referência.
- `README.full.md`: guia completo (macro → micro). Documentação detalhada da arquitetura, endpoints, exemplos e comandos.
 - Recent changes: added Test UI examples and a small engine behaviour change (borderline carga_horaria => ANALISE_HUMANA). See [README.full.md](README.full.md) and [app/templates/test_ui.html](app/templates/test_ui.html#L1).
- `README.deploy.md`: instruções e checklist para deploy em produção (variáveis sensíveis, migrations, backups, workers, observabilidade).
- `DEVELOPER.md`: guia de desenvolvimento local (venv, instalar deps, rodar, debug, como adicionar mappers e regras).
- `API_EXAMPLES.md`: exemplos práticos de chamadas à API (curl e Python) e exemplos de payload/response. Veja também `DOCS/USAGE.md` para guia rápido e notas sobre `X-API-Key`.
- `INTEGRATION_DVP.md`: guia de integração com Document Validation Platform (DVP) — configuração, API keys, smoke tests, arquitetura e troubleshooting.
- `RUNBOOK.md`: runbook operacional com troubleshooting rápido, comandos para checagens e procedimentos de manutenção.
- `CONTRIBUTING.md`: orientações para contribuir (PRs, estilo, testes).
- `CHANGELOG.md`: changelog (seção Unreleased para alterações recentes).
- `SECURITY.md`: recomendações de segurança e práticas para segredos e rotação.

Arquivos de configuração e ambiente:

- `.env` / `.env.example`: variáveis de ambiente (DB, Redis, URLs de mappers, chaves de API). Nunca comitar segredos reais.
- `docker-compose.yml`: compose para desenvolvimento (web, mock-embed, mock-llm, redis, postgres).
- `docker-compose.prod.yml`: compose orientado para produção (usa variáveis `${...}`).
- `Dockerfile`: imagem da aplicação.
- `pyproject.toml` / `requirements.txt`: dependências do projeto.

Código (principais módulos):

- `app/config.py`: carrega configurações / variáveis de ambiente.
- `app/db.py`: inicializa engine do SQLAlchemy com `DATABASE_URL`.
- `app/redis_client.py`: cria cliente Redis a partir de `REDIS_URL`.
- `app/seed.py`: script para popular dados de exemplo (API keys, tenants) — usado em dev.
- `app/main.py` / `app/asgi.py`: entrypoint da aplicação.
- `app/api/routes.py`: endpoints principais (ex.: `POST /v1/equivalences/evaluate`).
- `app/api/batch_routes.py`: endpoints para processamento em lote (enfileiramento).
- `app/worker.py`: lógica de processamento de jobs consumidos pela fila RQ.
- `app/queue.py`: fábrica/integração com RQ e enfileiramento.
- `app/engine/`: núcleo do motor (regras, scoring, justificativas).
- `app/mapper/`: implementações de mappers (stub, embedding+LLM, openai, fallback).
- `alembic/`: migrações do banco (use `alembic upgrade head`).

Testes e qualidade:

- `tests/`: testes unitários de componentes (usar `pytest`).
- `pytest.ini`: configuração do pytest.

Operação/infra:

- `pgdata` volume (definido no compose) — persistência do Postgres.
- Backup/restore: exemplos no `README.deploy.md` (uso de `pg_dump` ou soluções gerenciadas).

Como usar este índice

- Para um rápido start: leia `README.md` e siga o bloco "Configuração rápida".
- Para entender a arquitetura e exemplos aprofundados: consulte `README.full.md`.
- Para deploy em produção: consulte `README.deploy.md` e `SECURITY.md`.
- Para desenvolvimento e contribuições: consulte `DEVELOPER.md` e `CONTRIBUTING.md`.

Se quiser, eu posso:
- adicionar links cruzados no topo de cada documento apontando para este `INDEX.md`,
- gerar um sumário automático com links para seções internas, ou
- abrir um PR com essas alterações prontas. 
