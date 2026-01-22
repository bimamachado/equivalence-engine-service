# Algoritmo de Decisão (DEFERIR / INDEFERIR / COMPLEMENTO / ANÁLISE HUMANA)

Este documento descreve com detalhe o fluxo do algoritmo que decide `DEFERIDO`, `INDEFERIDO`, `COMPLEMENTO` ou `ANALISE_HUMANA`, o formato JSON de entrada/saida e em que momento a LLM/mapper é acionada.

Resumo rápido do fluxo (implementação em `app/engine/service.py`):

1. Validação básica e carregamento da taxonomia.
2. Aplicação de *hard rules* determinísticas (regras que podem indeferir sem IA).
   - Se alguma regra bloqueante falhar → `INDEFERIDO` imediato.
3. Mapeamento (mapper primário; cache; fallback opcional).
   - Aqui é onde o LLM/embeddings é chamado: o `mapper.map(...)` converte a ementa em conceitos da taxonomia.
   - Se o mapper primário não retornar resultados e `options.allow_degraded_fallback=True`, o `fallback_mapper` é chamado e `degraded_mode=True`.
4. Construção de vetores, cobertura, cobertura crítica e penalidade por nível.
5. Cálculo do `score` final e *breakdown*.
6. Decisão final: lógica de borderline (carga horária) e chamada de `decide(...)`.
7. Construção de justificativas (curta e detalhada) e evidências opcionais.
8. Auditoria (gravação de evento no repositório de audit).

Entrada (EvaluateRequest) — campos principais

- `request_id` (string): id único da requisição.
- `origem`, `destino` (objeto `DisciplineInput`): cada disciplina contém:
  - `nome` (string)
  - `carga_horaria` (int)
  - `ementa` (string) — texto que será mapeado
  - `aprovado` (bool opcional), `nivel` (basico/intermediario/avancado)
  - `ano_conclusao`, `disciplina_id` (opcionais)
- `policy` (`PolicyInput`) — parâmetros que afetam decisão:
  - `min_score_deferir` (0-100)
  - `min_score_complemento` (0-100)
  - `tolerancia_carga` (float 0..1) — ex: 1.0 exige carga >= destino; 0.8 aceita 80%
  - `exigir_criticos` (bool) — se true e cobertura crítica < 1.0 → `INDEFERIDO` na decisão
  - `confidence_cutoff` — filtra conceitos por confiança
- `taxonomy_version`, `policy_version` (strings)
- `options` (`EvaluateOptions`): `return_evidence` (bool), `allow_degraded_fallback` (bool)

Exemplo de entrada (simplificado):

```json
{
  "request_id": "r-2026-0001",
  "origem": { "nome": "Algoritmos", "carga_horaria": 60, "ementa": "..." },
  "destino": { "nome": "Introdução a Programação", "carga_horaria": 75, "ementa": "..." },
  "policy": { "min_score_deferir": 85, "min_score_complemento": 70, "tolerancia_carga": 0.8 },
  "taxonomy_version": "2026.01",
  "policy_version": "v3",
  "options": { "return_evidence": true, "allow_degraded_fallback": true }
}
```

Saída (EvaluateResponse) — campos principais

- `request_id` (string)
- `decisao` (one of `DEFERIDO`, `INDEFERIDO`, `COMPLEMENTO`, `ANALISE_HUMANA`)
- `score` (0-100)
- `breakdown`: `{ cobertura, cobertura_critica, penalidade_nivel }` (valores 0..1)
- `hard_rules`: lista de resultados de verificação de regras (nome, ok, detalhes)
- `faltantes`, `criticos_faltantes`: listas de node ids não cobertos
- `justificativa_curta`, `justificativa_detalhada` (strings legíveis)
- `evidence` (opcional): blocos com conceitos cobertos (node_id, weight, confidence, evidence[])
- `degraded_mode` (bool), `model_version`, `policy_version`, `taxonomy_version`, `timings_ms`, `meta`

Exemplo (parcial):

```json
{
  "request_id":"r-2026-0001",
  "decisao":"ANALISE_HUMANA",
  "score":72,
  "breakdown":{"cobertura":0.6, "cobertura_critica":0.9, "penalidade_nivel":0.1},
  "hard_rules":[],
  "faltantes":[210,305],
  "criticos_faltantes":[305],
  "justificativa_curta":"Diferença de carga dentro da tolerância; complementar recomendado.",
  "justificativa_detalhada":"...",
  "evidence":{ /* EvidenceBlock */ },
  "degraded_mode": false,
  "model_version":"mapper-stub",
  "policy_version":"v3",
  "taxonomy_version":"2026.01",
  "timings_ms":{ /* tempos de cada etapa */ }
}
```

Detalhes do algoritmo

- Hard rules (`app/engine/hard_rules.py`): executa validações determinísticas (ex.: requisito de aprovação, validade temporal, carga mínima, input mínimo). Se `hard_rules_block_decision(...)` retornar true a execução para com `INDEFERIDO`.

- Mapeamento (chamada ao `mapper`):
  - Implementado por `app/mapper/*` (ex.: `embedding_llm_mapper.py`, `openai_mapper.py`, `stub_mapper.py`).
  - `mapper.map(tenant_id, taxonomy_version, ementa)` retorna uma lista de objetos mapeados com `node_id`, `weight`, `confidence`, `evidence`.
  - Se o mapper primário é baseado em embeddings/LLM, essa é a etapa que fará chamadas HTTP para serviços de embeddings/LLM.
  - Resultado é cacheado por hash do texto para evitar chamadas repetidas.
  - Se `mapped_o` ou `mapped_d` vierem vazios e `allow_degraded_fallback=True`, o sistema tenta o `fallback_mapper` e marca `degraded_mode=True`.

- Scoring (`app/engine/scoring.py`):
  - `build_vector` filtra conceitos por `confidence_cutoff` e monta vetores de conceito→peso.
  - `coverage` e `critical_coverage` comparam vetores origem↔destino e retornam listas de faltantes.
  - `final_score(policy, cov, cov_crit, pen)` aplica pesos e gera `score` (0-100) e `breakdown`.

- Decisão (`app/engine/decision.py`): ordem e regras:
  1. Se `degraded_mode == True` → `ANALISE_HUMANA` (conservador).
  2. Se `policy.exigir_criticos == True` e `cov_crit < 1.0` → `INDEFERIDO`.
  3. Se `score >= policy.min_score_deferir` → `DEFERIDO`.
  4. Se `score >= policy.min_score_complemento` → `COMPLEMENTO`.
  5. Caso contrário → `INDEFERIDO`.

- Regra de borderline por `carga_horaria` (implementada em `service.evaluate` antes de `decide`):
  - Calcula `min_required = ceil(destino.carga_horaria * tolerancia_carga)`.
  - Se `origem.carga_horaria < destino.carga_horaria` mas `origem.carga_horaria >= min_required` → `ANALISE_HUMANA` (prioriza revisão humana para casos de carga parecida).

Quando a LLM é chamada

- A LLM (ou serviço de embeddings/LLM) é acionada somente na etapa de `mapper.map(...)` quando o mapper configurado faz chamadas externas (ex.: `embedding_llm_mapper`, `openai_mapper`).
- A decisão/score em si é puramente lógica/numeric e NÃO chama a LLM: a LLM só fornece os conceitos/weights/confidences que alimentam o scoring.
- Se o mapper falhar (sem resultados) e `allow_degraded_fallback` desativado, o sistema seguirá com vetores vazios e a decisão será baseada nas regras conservadoras (provável `INDEFERIDO` ou `ANALISE_HUMANA`).

Boas práticas operacionais

- Teste com o `test-ui` e payloads de exemplo para verificar cenários `DEFERIDO`, `COMPLEMENTO`, `INDEFERIDO` e `ANALISE_HUMANA`.
- Ajuste `policy.min_score_deferir` e `min_score_complemento` para calibrar o trade-off entre automação e revisões humanas.
- Monitore `degraded_mode` e alertas do mapper/LLM; configure fallback apenas se aceitar revisões humanas posteriores.

Referências no código

- Implementação do fluxo: `app/engine/service.py`
- Hard rules: `app/engine/hard_rules.py`
- Scoring: `app/engine/scoring.py`
- Decisão: `app/engine/decision.py`
- Mappers: `app/mapper/` (ver `embedding_llm_mapper.py`, `openai_mapper.py`, `stub_mapper.py`)

---

Se quiser, posso também:
- adicionar exemplos JSON completos (entrada + saída) para 4 cenários (DEFERIDO/INDEFERIDO/COMPLEMENTO/ANALISE_HUMANA),
- ou criar scripts em `scripts/` que rodem esses exemplos automaticamente contra a instância local.
