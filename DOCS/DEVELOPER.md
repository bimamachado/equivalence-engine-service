# Developer Guide

Setup local dev environment

**Recent changes (dev)**
- Test UI: see [app/templates/test_ui.html](app/templates/test_ui.html#L1) — contains full and minimal payloads for manual testing.
- Engine behavior: `app/engine/service.py` now forwards borderline carga_horaria cases to `ANALISE_HUMANA`. Add or update unit/integration tests if you rely on previous behaviour.
- Secrets: avoid storing `LLM_API_KEY` in `.env` in the repo; prefer a secrets manager or docker-compose secrets and rotate any key already committed.

1. Crie e ative o virtualenv

Linux / macOS / WSL:
```bash
python -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instale dependências
```bash
pip install -r requirements.txt
```

3. Copie e edite `.env`
```bash
cp .env.example .env
# editar variáveis locais (DATABASE_URL, REDIS_URL, etc.)
```

4. Aplicar migrations e popular dados dev
```bash
alembic upgrade head
python -m app.seed
```

Rodando a aplicação
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Rodando testes
```bash
pytest -q
```

Formato e lint
- Use `black` e `ruff` (ou as ferramentas que o projeto usa). Encoraje PRs limpos e pequenos.

Como adicionar um mapper
1. Crie arquivo em `app/mapper` implementando `BaseMapper`.
2. Registre no local de resolução (ver `app/mapper/__init__` ou ponto de construção do mapper).
3. Adicione testes unitários em `tests/`.
4. Atualize documentação se necessário.

Como adicionar uma regra de negócio
- Implemente em `app/engine/hard_rules.py` ou em módulos específicos.
- Garanta cobertura por testes unitários e integração se afetar endpoints.

Trabalhando com filas (RQ)
- Enfileire jobs via `app/queue.py` ou endpoints batch.
- Rode worker local para desenvolvimento:
```bash
rq worker -u redis://127.0.0.1:6379/0 equivalence
```

Debugging
- Use logs (`app/logging_setup.py`) e `uvicorn` em modo `--reload`.
- Para investigar jobs RQ: `rq info -u redis://localhost:6379/0`.
 Para investigar jobs RQ: `rq info -u redis://127.0.0.1:6379/0`.

Troubleshooting: worker e variáveis de ambiente
-----------------------------------------------

Se você ajustar variáveis em `.env` que afetem `REDIS_URL`, `DATABASE_URL`, `EMBED_URL` ou `LLM_URL`, o `worker` (container ou processo) precisa ser reiniciado para carregar as novas variáveis. Passos rápidos:

- Com Docker Compose:

```bash
# rebuild/recreate apenas o worker para aplicar novas envs
docker compose up -d --no-deps --force-recreate worker

# (opcional) ver logs do worker
docker compose logs --no-color --tail=200 worker
```

- Sem Docker (local):

```bash
source .venv/bin/activate
export REDIS_URL=redis://localhost:6379/0
export EMBED_URL=http://localhost:9001
export LLM_URL=http://localhost:9002
rq worker -u "$REDIS_URL" equivalence
```

Problemas comuns e como checar:

- Itens marcados como `failed` no painel de jobs: verifique os logs do `worker` e as mensagens de erro em `/v1/jobs/<job_id>/results`.
- `Connection refused` para `mock-embed` ou `mock-llm`: confirme se os serviços `mock-embed` e `mock-llm` estão `Up` no `docker compose ps` e se os `EMBED_URL`/`LLM_URL` apontam para `mock-embed:9001` e `mock-llm:9002` quando usando compose.
- Tabelas ausentes (`relation "api_keys" does not exist`): execute migrações ou chame `app.bootstrap.init_db()` dentro do container para criar as tabelas de desenvolvimento.

Adicionar essa breve seção evita quedas inesperadas no processamento em lote após mudanças de configuração.


