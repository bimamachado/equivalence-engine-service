# Workflows operacionais por decisão

Este documento descreve os fluxos operacionais que acontecem após cada decisão do motor: `DEFERIDO`, `INDEFERIDO` e `ANALISE_HUMANA`.

Para cada caso há: propósito, checklist de ações automáticas e manuais, e um template de justificativa que pode ser usado na UI ou em comunicações.

## 1) DEFERIDO

- Propósito: registrar e comunicar aprovação automática da equivalência sem intervenção humana.

- Checklist automático (sistema):
  1. Persistir resultado em tabela de equivalências/auditoria com `request_id`, `decisao`, `score`, `policy_version`, `taxonomy_version`, `model_version` e `timings_ms`.
  2. Gerar atividade de notificação para o aluno (email/SIS) com `justificativa_curta` e link para `justificativa_detalhada` e evidências.
  3. Atualizar status do pedido para `finalizado: aprovado` e gravar `meta`.
  4. Registrar logs e métricas (`equivalence_decisions_total{decision="DEFERIDO"}`).

- Ações manuais (opcionais):
  - Revisão pontual por auditoria (amostragem) para garantir qualidade.

- Template de justificativa (curta):

  DEFERIDO: Score e critérios atendidos para deferimento automático.

- Template de justificativa (detalhada):

  Decisão: DEFERIDO
  Motivo: Score e critérios atendidos para deferimento automático.
  Score final: {score}/100
  Cobertura: {breakdown.cobertura}
  Cobertura crítica: {breakdown.cobertura_critica}
  Penalidade de nível: {breakdown.penalidade_nivel}
  Observações: {meta.*}

## 2) INDEFERIDO

- Propósito: recusar automaticamente quando requisitos mínimos não são atendidos.

- Checklist automático (sistema):
  1. Persistir resultado com `decisao=INDEFERIDO` e `hard_rules` detalhadas.
  2. Notificar o aluno com `justificativa_curta` e link para `justificativa_detalhada` explicando os motivos (conceitos críticos faltantes, score insuficiente etc.).
  3. Criar registro de recurso/opção para reavaliação (se política permitir), com instruções sobre evidências necessárias.
  4. Atualizar métricas (`equivalence_decisions_total{decision="INDEFERIDO"}`).

- Ações manuais recomendadas:
  - Permitir envio de recurso com documentação adicional (programas de disciplina, portfólios, históricos).
  - Em casos recorrentes, analisar ajustes de `policy` ou mapeador.

- Template de justificativa (curta):

  INDEFERIDO: Score insuficiente para equivalência ou falha em regra obrigatória.

- Template de justificativa (detalhada):

  Decisão: INDEFERIDO
  Motivo: {motivo_from_engine}
  Score final: {score}/100
  Conceitos críticos faltantes: {criticos_faltantes}
  Ações possíveis: submissão de evidências / complemento / recurso.

## 3) ANÁLISE_HUMANA

- Propósito: encaminhar casos que antes seriam marcados como `COMPLEMENTO` para revisão humana, garantindo checagem manual antes de qualquer ação automatizada.

- Checklist automático (sistema):
  1. Persistir resultado com `decisao=ANALISE_HUMANA` e lista de lacunas (`faltantes`).
  2. Marcar caso para triagem humana e indexar evidências para o avaliador.
  3. Notificar avaliadores/triagem com prioridade e instruções de revisão.
  4. Gerar entrada em workflow de acompanhamento (ex.: `analise_humana_pending`).

- Ações manuais recomendadas:
  - Avaliador identifica atividades/prazos e, se aplicável, propõe plano de complemento.
  - Ao receber evidências, avaliador decide entre `DEFERIDO`, `INDEFERIDO` ou solicitar complemento específico.

- Template de justificativa (curta):

  ANALISE_HUMANA: Caso encaminhado para revisão humana devido a lacunas ou necessidade de verificação manual.

- Template de justificativa (detalhada):

  Decisão: ANALISE_HUMANA
  Motivo: {motivo_from_engine}
  Score final: {score}/100
  Lacunas identificadas (node ids): {faltantes}
  Recomendação: {descricao_do_complemento} (ex.: cursar módulo X, entregar plano de estudos Y) — decisão final depende da análise humana.

Checklist para reavaliação após intervenção humana:
  - Receber comprovante/atividade/documento (quando aplicável).
  - Avaliador valida se conteúdo cobre os `faltantes` citados.
  - Decisão final: `DEFERIDO` se score >= `min_score_deferir` ou `INDEFERIDO` caso contrário; avaliador pode também requisitar complemento e agendar reavaliação.

## 4) ANÁLISE_HUMANA

- Propósito: encaminhar casos incertos ou sensíveis para revisão humana.

- Quando acionar (exemplos):
  - `degraded_mode == True` (mapper primário indisponível),
  - borderline por `carga_horaria` (origem dentro da tolerância mas menor que destino),
  - evidências conflitantes ou pouca confiança mesmo com score próximo ao limiar,
  - presença de regras administrativas que exigem revisão local.

- Checklist para triagem inicial (sistema / triador):
  1. Agrupar e exibir as evidências relevantes: `evidence.covered_concepts`, `faltantes`, `criticos_faltantes`.
  2. Incluir metadados: `origem.nome`, `destino.nome`, `carga_horaria`, `policy_version`, `model_version`.
  3. Fornecer acesso ao texto original (`ementa`) e trechos usados como `evidence`.

- Checklist detalhado para avaliador humano:
  1. Verificar integridade do pedido e documentos anexos (programa, ementa, atividades).
  2. Conferir `hard_rules` e confirmar se alguma regra administrativa exige ação.
  3. Revisar `covered_concepts` e `missing_concepts` com a taxonomia; identificar se lacunas são formais ou substantivas.
  4. Considerar equivalência por conteúdo: comparar objetivos e tópicos centrais.
   5. Decidir entre: `DEFERIDO`, `INDEFERIDO` ou `ANALISE_HUMANA` (pode também solicitar mais informações).
  6. Registrar justificativa detalhada e ações (aprovar, negar, exigir complemento, anexar observações administrativas).

- Template de nota do avaliador (para registrar na aplicação):

  Avaliador: {nome_avaliador}
  Data: {YYYY-MM-DD}
  Decisão: {DEFERIDO|INDEFERIDO|ANALISE_HUMANA}
  Racional: {texto explicando motivos, com referências a tópicos/trechos da ementa}
  Ações: {ex.: emitir equivalência / exigir complemento X / abrir recurso}

---

