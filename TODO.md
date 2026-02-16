# TODO — Equivalence Engine Service

## ✅ Histórico Recente

### 2026-02-13
- ✅ **Documentação**: Criação de docs espelhados do document-validation-platform:
  - README-FIRST.md, TODO.md, URL_USER.md
  - docs/TECNOLOGIAS.md, docs/operations/dev_run.md, docs/operations/cheatsheet.md
  - docs/runbooks/operations.md, docs/runbooks/incident_response.md
  - docs/deploy.md, docs/SMOKE_TEST.md, docs/SCRIPTS_GUIDE.md

### Histórico anterior
- ✅ Motor de equivalência com regras hard-coded e scoring
- ✅ Suporte a embeddings + LLM (mappers configuráveis)
- ✅ API REST com autenticação por API Key
- ✅ Processamento batch via RQ (Redis Queue)
- ✅ Test UI com exemplos DEFERIDO/INDEFERIDO/ANALISE_HUMANA
- ✅ Borderline carga_horaria → ANALISE_HUMANA

---

## 🔄 Pendências Prioritárias

### Testes
1. Adicionar smoke test automatizado em pipeline CI/CD
2. Aumentar cobertura de testes unitários (engine, mappers)
3. Testes de integração para batch processing

### Infraestrutura
1. Adicionar Prometheus/Grafana ao docker-compose (opcional)
2. Documentar métricas expostas em `/metrics`
3. Configurar health checks robustos (DB + Redis)

### Mappers e IA
1. Implementar mappers reais (OpenAI, Anthropic) além dos stubs
2. Cache de embeddings para reduzir custos
3. Fallback mapper: documentar comportamento degradado

### API e Segurança
1. Rotação de API keys: procedimento documentado
2. Rate limiting por tenant
3. Auditoria de chamadas (já existe audit repository)

---

## 📋 Status por Componente

### Engine
- ✅ Regras hard-coded
- ✅ Scoring (coverage, critical_coverage, level_penalty)
- ✅ Justificativas
- ✅ Borderline handling (carga_horaria → ANALISE_HUMANA)

### Mappers
- ✅ Stub mapper (dev)
- ✅ Embedding + LLM mapper (configurável)
- ✅ Fallback mapper (modo degradado)
- ⏳ OpenAI/Anthropic: configurar com chaves reais

### API
- ✅ POST /v1/equivalences/evaluate
- ✅ Batch endpoint
- ✅ Admin/DLQ endpoints
- ✅ Test UI (/test)
- ✅ /health, /metrics

### Workers (RQ)
- ✅ Worker RQ para jobs batch
- ✅ Hooks para failed jobs
- ⏳ DLQ: procedimentos de reprocessamento documentados

### Storage
- ✅ PostgreSQL (auditoria, tenants, api_keys)
- ✅ Redis (fila RQ, cache)
- ✅ Alembic migrations

---

## 🎯 Próximos Passos Sugeridos

1. **CI/CD**: Adicionar GitHub Actions ou similar para testes e lint
2. **Observabilidade**: Expor métricas Prometheus e (opcional) dashboard Grafana
3. **Documentação**: Manter README-FIRST e docs sincronizados
4. **Integração**: Testar consumo pelo document-validation-platform (EQUIVALENCY_URL)
5. **Performance**: Benchmark de latência do endpoint evaluate
