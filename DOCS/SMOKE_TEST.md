# Smoke Test — Equivalence Engine Service

Este documento descreve como validar o sistema com smoke tests.

---

## Resumo

O smoke test verifica que:

1. A API está respondendo (`/health`)
2. A autenticação por API Key funciona
3. O endpoint `POST /v1/equivalences/evaluate` retorna uma decisão válida (DEFERIDO, INDEFERIDO ou ANALISE_HUMANA)

---

## Pré-requisitos

- Serviços rodando via `docker compose` (web, postgres, redis, mocks)
- API key criada (`python -m app.seed`)
- `curl` e `jq` instalados (opcional, para formatação)

---

## Passo a passo

### 1. Health check

```bash
curl -sS http://localhost:8000/health
```

Esperado: `{"status":"ok"}` ou similar (HTTP 200)

---

### 2. Teste de avaliação (payload mínimo)

```bash
curl -sS -X POST http://localhost:8000/v1/equivalences/evaluate \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-admin-abc123' \
  -d '{
    "request_id":"smoke-001",
    "origem":{
      "nome":"Algoritmos",
      "carga_horaria":60,
      "ementa":"Estruturas de dados e algoritmos.",
      "aprovado":true,
      "nivel":"intermediario"
    },
    "destino":{
      "nome":"Introdução a Programação",
      "carga_horaria":60,
      "ementa":"Lógica de programação e estruturas básicas.",
      "nivel":"basico"
    },
    "policy":{"min_score_deferir":85},
    "taxonomy_version":"2026.01"
  }' | jq .
```

Esperado: resposta com `decisao` (DEFERIDO, INDEFERIDO ou ANALISE_HUMANA), `score`, `justificativa_*`, etc.

---

### 3. Script de teste

O projeto possui um script em `scripts/test_api.sh`:

```bash
bash scripts/test_api.sh
```

Verifique o conteúdo do script para ver o payload e validações utilizadas.

---

### 4. Test UI (navegador)

Acesse http://localhost:8000/test para testar manualmente com exemplos pré-definidos de DEFERIDO, INDEFERIDO e ANALISE_HUMANA.

---

## Cenários de teste

| Cenário        | Payload                          | Decisão esperada     |
|----------------|----------------------------------|-----------------------|
| Alta similaridade | carga_horaria iguais, ementas próximas | DEFERIDO (score alto) |
| Baixa similaridade | carga_horaria diferentes, ementas distantes | INDEFERIDO (score baixo) |
| Borderline     | score entre thresholds           | ANALISE_HUMANA        |

---

## Falhas comuns

- **401 Unauthorized**: API Key inválida ou ausente. Rodar `python -m app.seed`.
- **500 Internal Server Error**: Ver logs do web (`docker compose logs web`). Pode ser mapper (EMBED_URL/LLM_URL) indisponível.
- **Connection refused**: API não está rodando. Verificar `docker compose ps`.

---

## Integração com document-validation-platform

Se o Equivalence Engine for consumido pelo document-validation-platform:

1. Configure `EQUIVALENCY_URL` no `.env` do DVP para apontar para este serviço (ex.: `http://localhost:8001` se usar porta 8001 para evitar conflito).
2. Rode o smoke test do DVP com case type `TRANSFER_CREDIT_EQUIVALENCY` para validar o fluxo end-to-end.
