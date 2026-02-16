# Guia de Scripts — Equivalence Engine Service

Este documento descreve os scripts disponíveis na pasta `scripts/` do projeto.

---

## Visão geral

| Script | Propósito | Uso típico |
|--------|-----------|------------|
| `seed_safe.py` | Popular dados (tenants, API keys) de forma segura | Setup inicial, dev |
| `check_keys.py` | Verificar/gerar API keys | Admin, troubleshooting |
| `run_post.py` | Enviar requisição POST para a API | Testes manuais |
| `test_api.sh` | Smoke test da API | Validação E2E |
| `sweep_openapi.py` | Testar todos os endpoints OpenAPI | Validação de contrato |
| `print_db.py` | Inspecionar estado do banco | Debug |
| `create_tables.py` | Criar tabelas (alternativa ao Alembic) | Setup legado |
| `generate_docs_index.py` | Gerar índice de documentação | Manutenção de docs |
| `patch_batch_worker.py` | Patch/correção para worker batch | Manutenção |
| `run_api_tests.ps1` | Rodar testes (PowerShell) | Windows |

---

## Scripts em detalhe

### seed_safe.py

**Propósito:** Popular o banco com tenants e API keys de exemplo de forma segura (sem sobrescrever dados existentes).

**Uso:**
```bash
python scripts/seed_safe.py
# ou
python -m app.seed  # se o seed estiver em app/seed.py
```

**Notas:** Requer `DATABASE_URL` e `API_KEY_SALT` configurados. Cria chaves como `dev-admin-abc123`, `dev-tenant-abc123`, etc.

---

### check_keys.py

**Propósito:** Verificar existência e validade de API keys, ou gerar novas chaves.

**Uso:**
```bash
python scripts/check_keys.py [opções]
```

**Notas:** Consulte `--help` para opções. Útil para troubleshooting de autenticação.

---

### run_post.py

**Propósito:** Enviar uma requisição POST para um endpoint da API (ex.: `/v1/equivalences/evaluate`).

**Uso:**
```bash
python scripts/run_post.py [URL] [payload_file]
# Exemplo:
python scripts/run_post.py http://localhost:8000/v1/equivalences/evaluate scripts/test_payload.json
```

**Notas:** Requer `X-API-Key` configurado (env ou argumento). Payload em JSON.

---

### test_api.sh

**Propósito:** Smoke test automatizado — health check e chamada de avaliação.

**Uso:**
```bash
bash scripts/test_api.sh
```

**Notas:** Ajuste `API_KEY` e `BASE_URL` no script ou via variáveis de ambiente se necessário.

---

### sweep_openapi.py

**Propósito:** Varrer todos os endpoints documentados no OpenAPI e testar respostas (ex.: 200 OK).

**Uso:**
```bash
python scripts/sweep_openapi.py
# Base URL pode ser configurada via env ou argumento
```

**Notas:** Gera relatório em `/tmp/openapi_sweep_report.json`. Útil para validação de contrato em CI.

---

### print_db.py

**Propósito:** Inspecionar estado do banco (tabelas, contagens, amostras).

**Uso:**
```bash
python scripts/print_db.py
```

**Notas:** Usa `app.config` e `app.db`. Útil para debug rápido.

---

### create_tables.py

**Propósito:** Criar tabelas diretamente via SQLAlchemy (sem Alembic).

**Uso:**
```bash
python scripts/create_tables.py
```

**Notas:** Preferir `alembic upgrade head` para migrations. Este script pode ser legado.

---

### generate_docs_index.py

**Propósito:** Gerar índice ou sumário da documentação.

**Uso:**
```bash
python scripts/generate_docs_index.py
```

**Notas:** Ajuste conforme estrutura de docs do projeto.

---

### patch_batch_worker.py

**Propósito:** Aplicar patch ou correção específica no worker de batch.

**Uso:**
```bash
python scripts/patch_batch_worker.py [opções]
```

**Notas:** Consulte o script para contexto. Pode ser temporário até correção no código principal.

---

### run_api_tests.ps1

**Propósito:** Rodar testes da API no Windows (PowerShell).

**Uso:**
```powershell
.\scripts\run_api_tests.ps1
```

**Notas:** Equivalente a `pytest tests/` em ambiente Windows.

---

## Dependências

A maioria dos scripts requer:

- Python 3.10+
- Variáveis de ambiente: `DATABASE_URL`, `REDIS_URL`, `API_KEY_SALT` (conforme o script)
- Pacotes: `requests`, `psycopg2`, etc. (instalados via `requirements.txt`)

---

## Ordem sugerida para setup

1. `alembic upgrade head` — migrations
2. `python -m app.seed` ou `scripts/seed_safe.py` — dados iniciais
3. `bash scripts/test_api.sh` — validar smoke test
4. `python scripts/sweep_openapi.py` — validar todos os endpoints (opcional)
