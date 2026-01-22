# Runbook (Operações / Troubleshooting)

## Verificações rápidas
- API:
  - `curl -I http://127.0.0.1:8001/health` (ou endpoint de readiness)
- Postgres:
  - `docker compose ps` / `pg_isready` / conectar com psql
- Redis:
  - `redis-cli ping`

## Problemas comuns

### Worker não processa jobs
1. Verifique se o Redis está disponível (`redis-cli ping`).
2. Verifique a fila (`rq info -u <REDIS_URL>`).
3. Inicie um worker em modo foreground para ver logs:
```bash
rq worker -u redis://127.0.0.1:6379/0 equivalence
```

### Jobs presos (DLQ)
- Verifique `app/rq_hooks.py` e endpoints admin (`app/admin_dlq_routes.py`) para reprocessamento.
- Reprocessar manualmente: recuperar payload e re-enfileirar com `queue.enqueue` ou via endpoint admin.

### Falha de conexão com DB
- Verifique `DATABASE_URL` e se Postgres está up.
- Logs do Postgres (docker logs) mostram erros de autenticação/permissão.

### Migrations falharam
- Verifique a versão do alembic e o estado das tabelas `alembic_version`.
- Se necessário, restaurar backup antes de aplicar correções.

## Rotinas de manutenção
- Backup diário: `pg_dump` ou estratégia de backup contínuo.
- Limpeza de filas antigas e logs grandes.

**Operational notes (recent changes)**
- The Test UI at [app/templates/test_ui.html](app/templates/test_ui.html#L1) provides manual payloads to reproduce DEFERIDO / INDEFERIDO / ANALISE_HUMANA scenarios.
- If you see unexpected human-review routes, check `app/engine/service.py` for the borderline `carga_horaria` handling.
- Security: if `LLM_API_KEY` was added to `.env`, rotate it immediately and move secrets to a secure store.

## Contato e escalonamento
- Primeiro nível: desenvolvedor responsável
- Segundo nível: time de infra (DB/redis)

