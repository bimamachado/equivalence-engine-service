# Integração com Document Validation Platform (DVP)

Este documento descreve como integrar o **Equivalence Engine Service** com o **Document Validation Platform** (DVP) para suportar análise de equivalência de créditos acadêmicos.

---

## 📋 Visão Geral

O DVP consome o Equivalence Engine através da API REST `/v1/equivalences/evaluate` para:

- **Avaliar equivalência** entre disciplinas cursadas e disciplinas destino
- **Obter decisões automáticas** (DEFERIDO/INDEFERIDO/ANALISE_HUMANA)
- **Receber justificativas** detalhadas para cada avaliação
- **Validar hard rules** (carga horária mínima, cobertura de conteúdo, etc.)

---

## 🔧 Configuração

### 1. API Key para DVP

O Equivalence Engine usa **API Keys com hash** para autenticação. A key padrão para integração com DVP é:

```
dvp_live_4PvMicqMbmZ4fQ4LKr4wW3uCe0OeUTPOGO2QMkTPN77S7d1e
```

#### Configuração no `.env`

```bash
DVP_API_KEY=dvp_live_4PvMicqMbmZ4fQ4LKr4wW3uCe0OeUTPOGO2QMkTPN77S7d1e
```

#### Seed Automático

A key é criada automaticamente pelo `app/seed.py` quando você executa:

```bash
docker compose exec web python -m app.seed
```

Ou manualmente:

```python
from app.db import SessionLocal
from app.security import hash_api_key
from app.models import ApiKey
import uuid

db = SessionLocal()
key_hash = hash_api_key('dvp_live_4PvMicqMbmZ4fQ4LKr4wW3uCe0OeUTPOGO2QMkTPN77S7d1e')
api_key = ApiKey(
    id=str(uuid.uuid4()),
    tenant_id='arbe',
    name='dvp-live-key',
    key_hash=key_hash,
    role='admin',
    status='active'
)
db.add(api_key)
db.commit()
db.close()
```

---

## 🌐 Endpoints de Integração

### POST `/v1/equivalences/evaluate`

Avalia equivalência entre disciplinas.

**Headers:**
```http
Content-Type: application/json
X-API-Key: dvp_live_4PvMicqMbmZ4fQ4LKr4wW3uCe0OeUTPOGO2QMkTPN77S7d1e
```

**Request Body:**
```json
{
  "request_id": "req-123",
  "origem": {
    "nome": "Fundamentos de Administração",
    "carga_horaria": 80,
    "ementa": "Teorias administrativas, planejamento estratégico...",
    "aprovado": true,
    "nivel": "graduacao",
    "ano_conclusao": 2023
  },
  "destino": {
    "nome": "Introdução à Administração",
    "carga_horaria": 60,
    "ementa": "Conceitos básicos de administração...",
    "nivel": "graduacao"
  },
  "policy": {
    "min_score_aceitar": 85,
    "min_score_revisar": 70,
    "tolerancia_carga_horaria": 0.8,
    "weights": {
      "semantic_similarity": 0.4,
      "keyword_overlap": 0.3,
      "taxonomy_coverage": 0.3
    },
    "confidence_cutoff": 0.75
  },
  "taxonomy_version": "2026.01",
  "policy_version": "v1"
}
```

**Response (200 OK):**
```json
{
  "request_id": "req-123",
  "decisao": "DEFERIDO",
  "score": 92,
  "breakdown": {
    "semantic_similarity": 0.88,
    "keyword_overlap": 0.85,
    "taxonomy_coverage": 0.90
  },
  "hard_rules": [],
  "justificativa_curta": "DEFERIDO: Score e critérios atendidos para deferimento automático.",
  "justificativa_detalhada": "A disciplina de origem cobre 90% dos conceitos da disciplina destino...",
  "evidence": [
    {
      "tipo": "semantic_similarity",
      "valor": 0.88,
      "descricao": "Alta similaridade semântica entre as ementas"
    }
  ],
  "timings_ms": {
    "total": 1250,
    "embedding": 450,
    "semantic": 200,
    "taxonomy": 350,
    "hard_rules": 50,
    "decision": 200
  },
  "metadata": {
    "taxonomy_version": "2026.01",
    "policy_version": "v1",
    "engine_version": "1.0.0"
  }
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "origem", "carga_horaria"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Invalid API key"
}
```

---

## 🔍 Smoke Tests

O DVP inclui smoke tests para validar a integração:

```bash
cd document-validation-platform
./scripts/smoke_test_equivalency.sh
```

### Cenários Testados:

1. ✅ **Disciplinas similares** → Espera DEFERIDO
2. ✅ **Disciplinas divergentes** → Espera score baixo
3. ✅ **Carga horária insuficiente** → Espera INDEFERIDO (hard rule)
4. ✅ **Idempotência** → Mesma decisão em chamadas repetidas
5. ✅ **Validação de input** → HTTP 422 para payload inválido
6. ✅ **Autenticação** → HTTP 401 para API key inválida
7. ✅ **Health check** → Verifica serviço disponível

### Graceful Degradation

Se o Equivalence Engine estiver **indisponível**, os smoke tests do DVP:
- ⚠️ Mostram warning (não falham)
- Exit code 0 (não quebram pipeline CI/CD)
- Sugerem como subir o serviço

---

## 🏗️ Arquitetura de Integração

```
┌─────────────────────────────────────┐
│  Document Validation Platform       │
│  ┌─────────────────────────────┐   │
│  │  Decision API (port 8000)   │   │
│  │  - Recebe casos de análise   │   │
│  │  - Orquestra workflows       │   │
│  └──────────┬──────────────────┘   │
│             │ HTTP POST            │
└─────────────┼──────────────────────┘
              │
              │ /v1/equivalences/evaluate
              │ X-API-Key: dvp_live_...
              ▼
┌─────────────────────────────────────┐
│  Equivalence Engine Service         │
│  ┌─────────────────────────────┐   │
│  │  FastAPI Web (port 8100)    │   │
│  │  - Valida API key            │   │
│  │  - Enfileira job (RQ)        │   │
│  └──────────┬──────────────────┘   │
│             │                       │
│  ┌──────────▼──────────────────┐   │
│  │  Worker (RQ)                 │   │
│  │  - Embeddings                │   │
│  │  - Semantic similarity       │   │
│  │  - Taxonomy mapping          │   │
│  │  - Hard rules                │   │
│  │  - Decision engine           │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  PostgreSQL (port 5433)     │   │
│  │  - API keys (hashed)         │   │
│  │  - Taxonomy                  │   │
│  │  - Results                   │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Redis (port 6380)          │   │
│  │  - RQ job queue              │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 🚀 Deploy

### Portas Utilizadas

| Serviço         | Porta | Descrição                |
|----------------|-------|--------------------------|
| Web API        | 8100  | HTTP API                 |
| PostgreSQL     | 5433  | Banco de dados           |
| Redis          | 6380  | Job queue (RQ)           |
| Mock Embed     | 9101  | Mock de embeddings (dev) |
| Mock LLM       | 9102  | Mock de LLM (dev)        |

### Docker Compose

```bash
cd equivalence-engine-service
docker compose up -d
```

### Health Check

```bash
curl http://localhost:8100/health
# {"status": "alive"}
```

---

## 🔐 Segurança

### API Key Management

Em **produção**, gere uma key segura:

```bash
python -c "import secrets; print('dvp_prod_' + secrets.token_urlsafe(48))"
```

Configure no DVP:

```bash
# document-validation-platform/.env
EQUIVALENCY_URL=https://equivalence.example.com
EQUIVALENCY_API_KEY=dvp_prod_<sua-key-segura>
```

E no Equivalence Engine:

```bash
# equivalence-engine-service/.env
DVP_API_KEY=dvp_prod_<sua-key-segura>
```

Recrie o banco:

```bash
docker compose exec web python -m app.seed
```

### HTTPS

Em produção, use HTTPS com certificado válido:

```nginx
server {
    listen 443 ssl http2;
    server_name equivalence.example.com;
    
    ssl_certificate /etc/letsencrypt/live/equivalence.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/equivalence.example.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8100;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📊 Monitoramento

### Métricas Expostas

- **Latência P50/P95/P99** de `/v1/equivalences/evaluate`
- **Taxa de erro** (4xx, 5xx)
- **Distribuição de decisões** (DEFERIDO/INDEFERIDO/ANALISE_HUMANA)
- **RQ queue depth** (jobs pendentes)

### Logs Estruturados

```json
{
  "timestamp": "2026-02-16T13:42:15.123Z",
  "level": "INFO",
  "service": "equivalence-engine",
  "request_id": "req-abc123",
  "decisao": "DEFERIDO",
  "score": 92,
  "duration_ms": 1250
}
```

---

## 🐛 Troubleshooting

### Problema: DVP recebe HTTP 401

**Causa:** API key inválida ou não configurada

**Solução:**
```bash
# Verifique se a key está no banco
docker compose exec web python -c "
from app.db import SessionLocal
from app.models import ApiKey
db = SessionLocal()
keys = db.query(ApiKey).filter(ApiKey.name == 'dvp-live-key').all()
print([k.name for k in keys])
"
```

### Problema: Timeout na chamada

**Causa:** Worker sobrecarregado ou embeddings lentos

**Solução:**
```bash
# Verifique queue do RQ
docker compose exec web rq info --config app.config
```

### Problema: Decisões inconsistentes

**Causa:** Taxonomy desatualizada ou policy incorreta

**Solução:**
```bash
# Verifique versão da taxonomy
docker compose exec web python -c "
from app.db import SessionLocal
from app.models import TaxonomyVersion
db = SessionLocal()
tv = db.query(TaxonomyVersion).filter(TaxonomyVersion.version == '2026.01').first()
print(f'Taxonomy: {tv.version}, Status: {tv.status}')
"
```

---

## 📚 Referências

- [API_EXAMPLES.md](API_EXAMPLES.md) → Exemplos de chamadas
- [DECISION.md](DECISION.md) → Lógica de decisão
- [WORKFLOWS.md](WORKFLOWS.md) → Fluxo de avaliação
- [SMOKE_TEST.md](SMOKE_TEST.md) → Testes de fumaça
- [SECURITY.md](SECURITY.md) → Práticas de segurança

---

## 🤝 Suporte

Para dúvidas ou problemas de integração, consulte:

1. **Smoke tests** do DVP: `scripts/smoke_test_equivalency.sh`
2. **Logs** do Equivalence Engine: `docker compose logs -f web worker`
3. **Dashboard** do RQ: `http://localhost:8100/rq` (se habilitado)
4. **Documentação DVP**: `document-validation-platform/docs/`
