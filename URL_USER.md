# URLs e Credenciais de Acesso - Equivalence Engine Service

Este documento contém todos os links e credenciais necessários para acessar os serviços do Equivalence Engine.

---

## 🚀 API Principal

**URL Base**: http://localhost:8000 (Docker) ou http://localhost:8001 (dev local)

**Documentação Interativa**: http://localhost:8000/docs (ou :8001)

**Health Check**: http://localhost:8000/health

**Métricas Prometheus**: http://localhost:8000/metrics

**Autenticação**: Header `X-API-Key` com API key válida

**Principais Endpoints**:
- `POST /v1/equivalences/evaluate` - Avaliar equivalência
- `POST /v1/equivalences/batch` - Processamento em lote
- `GET /health` - Health check
- `GET /metrics` - Métricas Prometheus

**Como obter API Key**:
```bash
python -m app.seed
# Ou use as chaves de exemplo: dev-admin-abc123, dev-tenant-abc123, etc.
```

---

## 🧪 Test UI

**URL**: http://localhost:8000/test (ou :8001/test)

**Credenciais**: Usar API Key no header ou no formulário

**Recursos**:
- Exemplos de payload para DEFERIDO, INDEFERIDO, ANALISE_HUMANA
- Teste manual de avaliação
- Payload mínimo e completo

---

## 🗄️ PostgreSQL - Database

**Host**: localhost (ou `postgres` dentro do Docker)

**Porta**: 5432

**Credenciais** (default dev):
- **Database**: `equivalence`
- **Usuário**: `equivalence`
- **Senha**: `equivalence` (ou valor em `POSTGRES_PASSWORD`)

**Connection String**:
```
postgresql://equivalence:equivalence@localhost:5432/equivalence
```

**Cliente CLI**:
```bash
docker compose exec postgres psql -U equivalence -d equivalence
```

---

## 📦 Redis - Cache e Fila RQ

**Host**: localhost (ou `redis` dentro do Docker)

**Porta**: 6379

**URL**: `redis://localhost:6379/0`

**Verificar conexão**:
```bash
redis-cli ping
# ou
docker compose exec redis redis-cli ping
```

**Inspecionar fila RQ**:
```bash
rq info -u redis://localhost:6379/0
```

---

## 🔧 Mock Services (Desenvolvimento)

### Mock Embed (embeddings)
**URL**: http://localhost:9001

**Função**: Stub para serviço de embeddings (usado quando EMBED_URL aponta para localhost:9001)

### Mock LLM
**URL**: http://localhost:9002

**Função**: Stub para serviço de LLM (resposta mock JSON)

**Configuração**: `EMBED_URL`, `LLM_URL` no `.env`

---

## 🔧 Scripts Úteis

### Popular dados (seed)
```bash
python -m app.seed
```

### Rodar migrations
```bash
alembic upgrade head
```

### Iniciar worker RQ
```bash
rq worker -u redis://localhost:6379/0 equivalence
```

### Smoke test
```bash
bash scripts/test_api.sh
```

---

## 📝 Notas Importantes

1. **Portas em Uso** (default):
   - 8000: API web (Docker)
   - 8001: API web (dev local, quando usa --port 8001)
   - 5432: PostgreSQL
   - 6379: Redis
   - 9001: Mock Embed
   - 9002: Mock LLM

2. **Variáveis de Ambiente**:
   - Todas as credenciais podem ser customizadas no arquivo `.env`
   - Verifique `prod.env.example` para variáveis disponíveis

3. **Conflito com document-validation-platform**:
   - Se rodar ambos no mesmo host, altere portas no equivalence:
   - 8000 → 8001 (API)
   - 9002 → 9012 (mock-llm, conflito com MinIO)
   - 5432, 6379: usar instâncias separadas ou containers com portas diferentes

4. **Documentação Adicional**:
   - Arquitetura: `DOCS/ARCHITECTURE/`
   - Operações: `docs/operations/`
   - Runbooks: `docs/runbooks/`

---

**Última atualização**: 13 de fevereiro de 2026
