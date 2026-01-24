# Algoritmo de Decisão (DEFERIR / INDEFERIDO / ANALISE_HUMANA)

Este documento descreve com detalhe o fluxo do algoritmo que decide `DEFERIDO`, `INDEFERIDO` ou `ANALISE_HUMANA`, o formato JSON de entrada/saida e em que momento a LLM/mapper é acionada.

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

## Taxonomia e Versões

- **Taxonomia:** conjunto canônico de categorias/labels usado para mapear texto (`ementa`) a `node_id` do grafo de conhecimento. Serve para normalizar entradas, suportar regras hard-coded e permitir indexação/consulta semântica.
- **`taxonomy_version`:** identifica a versão da taxonomia usada no processamento (ex.: `tax-v2025-11-01`, `2026.01`). Deve acompanhar cada decisão para permitir reavaliação ou auditoria quando a taxonomia mudar.

- **`version` (esquema):** versão do esquema do payload (ex.: `v1`, `v2`). Usada por validadores/parsers para compatibilidade.

- **`model_version`:** identifica o artefato de modelo usado no mapeamento/scoring (ex.: `openai-embed-1.2`, `mapper-embed+llm-0.1`). Essencial para reprodutibilidade e investigação de regressões.

- **`policy_version`:** versão da política de decisão (thresholds, flags, regras ativadas). Ex.: `policy-v3`. Deve constar em cada decisão para rastreabilidade e permitir rollback quando necessário.

Recomendações operacionais:
- Registrar `taxonomy_version`, `model_version` e `policy_version` por decisão e em logs de auditoria.
- Ao atualizar `model_version` ou `policy_version`, rodar testes controlados (A/B) e documentar impacto.
- Quando `taxonomy_version` muda de forma incompatível, considerar reindexação ou reprocessamento de históricos críticos e manter changelog de mapeamentos antigos→novos.

Exemplo mínimo de metadados incluídos no payload/registro:

```
{
  "version": "v2",
  "taxonomy_version": "tax-v2026-01",
  "model_version": "openai-embed-1.2",
  "policy_version": "policy-v3",
  "metadata": { ... }
}
```

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
- `decisao` (one of `DEFERIDO`, `INDEFERIDO`, `ANALISE_HUMANA`)
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
  4. Se `score >= policy.min_score_complemento` → `ANALISE_HUMANA`.
  5. Caso contrário → `INDEFERIDO`.

- Regra de borderline por `carga_horaria` (implementada em `service.evaluate` antes de `decide`):
  - Calcula `min_required = ceil(destino.carga_horaria * tolerancia_carga)`.
  - Se `origem.carga_horaria < destino.carga_horaria` mas `origem.carga_horaria >= min_required` → `ANALISE_HUMANA` (prioriza revisão humana para casos de carga parecida).

Quando a LLM é chamada

- A LLM (ou serviço de embeddings/LLM) é acionada somente na etapa de `mapper.map(...)` quando o mapper configurado faz chamadas externas (ex.: `embedding_llm_mapper`, `openai_mapper`).
- A decisão/score em si é puramente lógica/numeric e NÃO chama a LLM: a LLM só fornece os conceitos/weights/confidences que alimentam o scoring.
- Se o mapper falhar (sem resultados) e `allow_degraded_fallback` desativado, o sistema seguirá com vetores vazios e a decisão será baseada nas regras conservadoras (provável `INDEFERIDO` ou `ANALISE_HUMANA`).

Boas práticas operacionais

- Teste com o `test-ui` e payloads de exemplo para verificar cenários `DEFERIDO`, `INDEFERIDO` e `ANALISE_HUMANA`.
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
- adicionar exemplos JSON completos (entrada + saída) para 3 cenários (DEFERIDO/INDEFERIDO/ANALISE_HUMANA),
- ou criar scripts em `scripts/` que rodem esses exemplos automaticamente contra a instância local.

Arquivos Python principais envolvidos

 - `app/engine/service.py` — orquestra o fluxo completo (validação, regras, mapeamento, scoring, decisão, justificativa, auditoria).
 - `app/engine/hard_rules.py` — regras determinísticas que podem indeferir imediatamente.
 - `app/engine/scoring.py` — construção de vetores, cobertura, penalidades e cálculo do score final.
 - `app/engine/decision.py` — mapeia score/flags para decisão final.
 - `app/engine/justification.py` — gera justificativas legíveis (curta e detalhada).
 - `app/mapper/` — mappers que chamam LLM/embeddings (`embedding_llm_mapper.py`, `openai_mapper.py`, `stub_mapper.py`).
 - `app/taxonomy/store.py` — acesso à taxonomia (nós, relações, ids críticos).
 - `app/cache/cache.py` — cache local de mapeamentos por hash de texto.
 - `app/audit/repository.py` — grava eventos de auditoria/resultados.
 - `app/api/schemas.py` — Pydantic models (entrada/saída) usados pela API.
 - `app/main.py` — ponto de montagem da app (rotas, static files, middlewares).
 - `app/seed.py` — utilitário para popular chaves de API em dev.
 - `app/config.py` — configurações e leitura de variáveis de ambiente.

Configuração — exemplo de `.env`

Este serviço depende de variáveis de ambiente para conexão e comportamento. Exemplo mínimo para desenvolvimento:

```
DATABASE_URL=postgresql+psycopg2://equivalence:dev-equivalence-pass@127.0.0.1:5432/equivalence
REDIS_URL=redis://127.0.0.1:6379/0
RQ_QUEUE_NAME=equivalence

API_KEY_SALT=change-this-to-a-long-random-string
ADMIN_API_KEY=dev-admin-123
AUDITOR_API_KEY=dev-auditor-123
CLIENT_API_KEY=dev-client-123

EMBED_URL=http://127.0.0.1:9001
EMBED_API_KEY=
LLM_URL=http://127.0.0.1:9002
LLM_API_KEY=

# Optional: host/port used by local uvicorn run
HOST=127.0.0.1
PORT=8001
```

Notas de configuração

 - `API_KEY_SALT` é usada para hashear chaves de API; altere para um valor forte em produção.
 - `ADMIN_API_KEY`, `AUDITOR_API_KEY`, `CLIENT_API_KEY` são chaves de exemplo usadas pelo `app/seed.py` para popular dados de dev.
 - `EMBED_URL`/`LLM_URL` apontam para serviços externos de embeddings/LLM; o mapper chamará esses endpoints quando configurado para tal.
 - Em produção, use um secret manager (não comitar `.env` com segredos).

## Exemplo específico enviado (entrada) — explicação detalhada dos campos

Entrada de exemplo enviada para o motor (fornecida por você):

```json
{
  "request_id": "ex-deferido-001",
  "origem": {
    "instituicao": "Universidade Federal do Rio de Janeiro (UFRJ)",
    "codigo": "BCC310",
    "nome": "Banco de Dados",
    "carga_horaria": 60,
    "credito": 4,
    "nivel": "intermediario",
    "ementa": "Modelagem relacional, algebra relacional, SQL, normalização, transações e integridade.",
    "objetivos": [
      "Modelar bancos de dados",
      "Escrever consultas SQL complexas"
    ]
  },
  "destino": {
    "instituicao": "Universidade Estadual de Campinas (UNICAMP)",
    "codigo": "BCC343",
    "nome": "Sistemas de Banco de Dados",
    "carga_horaria": 60,
    "credito": 4,
    "nivel": "intermediario",
    "ementa": "Modelagem, SQL, índices, transações, e desempenho de bancos de dados.",
    "objetivos": [
      "Projetar esquemas relacionais",
      "Optimizar consultas"
    ]
  },
  "context": {
    "aluno": "Mariana Costa",
    "matricula": "201912345"
  },
  "taxonomy_version": "2026.01",
  "policy_version": "v3",
  "expected": "deferido"
}
```

Explicação campo-a-campo (entrada):

- `request_id`: identificador de correlação; usado em logs, auditoria e para ligar resposta/resultado à requisição original.
- `origem` / `destino`: objetos representando a disciplina cursada (`origem`) e a disciplina alvo (`destino`). O motor utiliza principalmente a `ementa` para mapeamento semântico (via mapper), e os demais campos para regras e transparência:
  - `instituicao`, `codigo`, `nome`: campos informativos para UI/audit; não alteram diretamente o matching sem regras explícitas.
  - `carga_horaria`: comparada à do destino para regras de `carga_horaria` e para a lógica de borderline/tolerância; afeta decisão automática quando há discrepância.
  - `credito`: campo informativo (pode ser usado em regras adicionais se configurado).
  - `nivel`: categorização (`basico`/`intermediario`/`avancado`) usada para calcular penalidade por nível quando aplicável.
  - `ementa`: texto livre que será enviado ao `mapper` — etapa em que a LLM/embeddings é chamada para extrair conceitos e confidences.
  - `objetivos`: lista opcional que pode ajudar mappers a priorizar conceitos e explicar correspondências.
- `context`: metadados operacionais (nome do aluno, matrícula, etc.) — importante para auditoria e histórico, não influencia a lógica do motor por padrão.
- `taxonomy_version`: versão da taxonomia usada para mapear `ementa` → `node_id`.
- `policy_version`: versão da política (thresholds e pesos) a ser utilizada na função `final_score` e `decide`.
- `expected`: campo EXTRAS (não parte do schema oficial) usado em testes que indica resultado esperado; não influencia o processamento.

## Exemplo específico retornado (saída) — explicação detalhada dos campos

Resposta fornecida pelo motor no exemplo:

```json
{
  "request_id": "ex-deferido-001",
  "decisao": "DEFERIDO",
  "score": 100,
  "breakdown": {
    "cobertura": 1,
    "cobertura_critica": 1,
    "penalidade_nivel": 0
  },
  "hard_rules": [
    { "rule": "input_minimo", "ok": true, "details": null },
    { "rule": "aprovacao", "ok": true, "details": null },
    { "rule": "carga_horaria", "ok": true, "details": null },
    { "rule": "validade_temporal", "ok": true, "details": "Não aplicável" },
    { "rule": "nivel", "ok": true, "details": "Não aplicável no MVP" }
  ],
  "faltantes": [],
  "criticos_faltantes": [],
  "justificativa_curta": "DEFERIDO: Score e critérios atendidos para deferimento automático.",
  "justificativa_detalhada": "Decisão: DEFERIDO\nMotivo: Score e critérios atendidos para deferimento automático.\nScore final: 100/100\nCobertura: 1.00\nCobertura crítica: 1.00\nPenalidade de nível: 0.00\nCarga horária: origem=60h, destino=60h",
  "evidence": {
    "covered_concepts": [
      { "node_id": 1001, "weight": 0.6569, "confidence": 0.7599, "evidence": [] },
      { "node_id": 1012, "weight": 0.6374, "confidence": 0.7462, "evidence": [] }
    ],
    "missing_concepts": [],
    "missing_critical_concepts": []
  },
  "degraded_mode": false,
  "model_version": "mapper-embed+llm-0.1",
  "policy_version": "v3",
  "taxonomy_version": "2026.01",
  "timings_ms": { "validate_ms": 0, "hard_rules": 0, "map": 1077, "score": 0, "decide": 0, "justify": 0, "total": 1077 },
  "meta": { "origin_vec_size": 2, "dest_vec_size": 2, "mapper_used": "primary" }
}
```

Explicação campo-a-campo (saída):

- `request_id`: igual ao de entrada para correlação.
- `decisao`: decisão final — aqui `DEFERIDO` indica que os thresholds e regras foram atendidos para aprovação automática.
- `score` (0-100): valor numérico final calculado pelo `final_score`.
- `breakdown`:
  - `cobertura`: 1 significa 100% dos conceitos relevantes do destino foram cobertos pela origem.
  - `cobertura_critica`: 1 significa que todos os conceitos marcados como críticos estão cobertos.
  - `penalidade_nivel`: 0 indica que não foi aplicada penalidade por diferença de nível.
- `hard_rules`: lista com o resultado de cada verificação determinística executada antes do mapeamento; `ok: true` mostra que a regra foi satisfeita. `details` pode conter observações (ex.: "Não aplicável").
- `faltantes` / `criticos_faltantes`: arrays vazios indicam que não há conceitos pendentes que impeçam o deferimento.
- `justificativa_curta` / `justificativa_detalhada`: explicações legíveis para UI/audit; a detalhada traz score e pontos relevantes.
- `evidence.covered_concepts`: mostras precisas dos `node_id` que contribuíram para a correspondência, com `weight` e `confidence` (fornecidos pelo mapper). `evidence` é um array de trechos/textos que justificam o mapeamento quando disponível.
- `degraded_mode`: false indica que o mapper primário funcionou corretamente (nenhum fallback).
- `model_version`: versão/identificador do mapper ou pipeline que gerou as correspondências.
- `timings_ms`: tempos por etapa; neste exemplo o passo `map` (chamada ao mapper/LLM) levou ~1077ms.
- `meta`: dados auxiliares (tamanhos dos vetores e qual mapper foi usado).

Interpretação prática deste caso

- Origem e destino têm `carga_horaria` idêntica (60) e `nivel` igual — por isso não há penalidade e a regra de carga passa.
- O mapper retornou conceitos suficientes com confiança acima do `confidence_cutoff`, resultando em `cobertura=1` e `score=100`.
- Como `policy.exigir_criticos` foi atendido (`cobertura_critica=1`), não há bloqueio crítico.
- Resultado final: `DEFERIDO` automático sem necessidade de revisão humana.

## Definições detalhadas das decisões

Esta seção explica, em linguagem operacional, o que significa cada decisão, quando é usada e qual o papel no fluxo de trabalho.

- `DEFERIDO`
  - O que é: decisão automática que aceita a equivalência entre a disciplina `origem` e a disciplina `destino` sem necessidade de intervenção humana.
  - Quando ocorre: quando todas as regras e thresholds aplicáveis são satisfeitos — isto é, `score >= policy.min_score_deferir`, cobertura crítica atendida (se exigida), e não existem bloqueios por *hard rules* ou por políticas de nível/carga.
  - Para que serve: permite processamento em escala sem aumentar o custo humano; gera um registro auditável e a justificativa detalhada para rastreabilidade.
  - Efeito operacional: o estudante recebe a equivalência aprovada; o sistema pode persistir o resultado no repositório de equivalências/auditoria.

- `INDEFERIDO`
  - O que é: decisão automática que rejeita a equivalência proposta.
  - Quando ocorre: quando falha alguma regra bloqueante (hard rule), ou quando o `score` é insuficiente (abaixo de `min_score_complemento`) ou quando conceitos críticos não foram contemplados e `policy.exigir_criticos` está ativo.
  - Para que serve: protege a integridade acadêmica evitando aprovações errôneas; sinaliza que a disciplina não atende os requisitos mínimos para equivalência.
  - Efeito operacional: a requisição é finalizada como rejeitada; o sistema deve fornecer justificativa detalhada para permitir recurso/manual review, se aplicável.

- Nota: a decisão anteriormente descrita como `COMPLEMENTO` passa a ser tratada como `ANALISE_HUMANA`.
  - Racional: cenários que ficariam em um estado intermediário e exigiriam complementos agora são encaminhados para revisão humana, para garantir checagem manual e evitar decisões automáticas parciais.
  - Quando aplicável: quando `score >= policy.min_score_complemento` mas `score < policy.min_score_deferir`, ou quando há faltantes que demandam intervenção humana.

- `ANALISE_HUMANA`
  - O que é: indicação de que o caso deve ser revisado por um avaliador humano (coordenador de curso, comissão ou equipe técnica).
  - Quando ocorre: usado em cenários conservadores ou ambíguos, incluindo, mas não limitado a:
    - `degraded_mode == True` (mapper primário falhou/indisponível),
    - regra de borderline de carga horária aplicada (origem dentro da tolerância mas menor que destino),
    - casos onde a política requer revisão manual por outras regras locais/administrativas,
    - quando o `score` ou as evidências não permitem uma conclusão confiável mesmo que thresholds sejam próximos.
  - Para que serve: garante que decisões sensíveis ou com risco de impacto sejam analisadas por humanos, preservando qualidade e conformidade acadêmica.
  - Efeito operacional: a requisição é colocada em uma fila de revisão humana (ou marcada para intervenção manual); o sistema deve expor um conjunto de evidências e a justificativa detalhada para facilitar a revisão.

Observações adicionais

- As decisões `DEFERIDO` e `INDEFERIDO` são projetadas para automação com níveis de confiança controlados por `policy`; casos de limiar intermediário são encaminhados para `ANALISE_HUMANA`.
- `ANALISE_HUMANA` é o mecanismo de defesa para cenários incertos ou quando o pipeline de IA está degradado; para reduzir o volume de `ANALISE_HUMANA` é comum calibrar `policy.min_score_deferir` e `min_score_complemento`, melhorar o mapper e usar evidências mais ricas.



