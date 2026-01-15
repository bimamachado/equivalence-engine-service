Diagrama ASCII (fluxo simplificado)

Cliente -> HTTP Endpoint -> `app/api/routes.py`
                             |
                             v
                       Validação (`pydantic`)
                             |
                             v
                    `app/engine/service.py` (orquestrador)
                             |
         +-------------------+-------------------+
         |                   |                   |
         v                   v                   v
    `mapper`            `scoring`            `decision`/
  (`app/mapper`)     (`app/engine/scoring.py`) `app/engine/decision.py`
         |                   |                   |
         +-------------------+-------------------+
                             |
                             v
                        Justificação
                        (`app/engine/justification.py`)
                             |
                             v
                        Persistência / Audit
                        (`app/repos.py`, `app/audit`)

Exemplos de payloads

Requisição (exemplo simplificado):

```json
{
  "request_id": "req-123",
  "origem": {
    "ementa": "Introdução a programação: variáveis, controle de fluxo",
    "carga_horaria": 60
  },
  "destino": {
    "ementa": "Fundamentos de programação: tipos, estruturas de controle",
    "carga_horaria": 60
  },
  "policy": {
    "confidence_cutoff": 0.3
  },
  "options": {
    "allow_degraded_fallback": true,
    "return_evidence": true
  }
}
```

Resposta (exemplo simplificado):

```json
{
  "request_id": "req-123",
  "decisao": "ACEITO",
  "score": 0.87,
  "breakdown": {"cobertura": 0.9, "cobertura_critica": 0.85, "penalidade_nivel": 0.05},
  "justificativa_curta": "Ocorrências suficientes...",
  "justificativa_detalhada": "Explicação passo a passo...",
  "evidence": {"covered_concepts": [], "missing_concepts": []},
  "degraded_mode": false
}
```

Notas rápidas:
- Use `options.allow_degraded_fallback` quando quiser tentar um mapper alternativo (mais genérico) ao primário.
- `policy.confidence_cutoff` controla o que é considerado "confiável" no mapeamento para cálculo de cobertura.

Se quiser que eu una este conteúdo ao arquivo principal `DOCS/MACRO_TO_MICRO.md`, eu aplico o patch direto no arquivo fonte.