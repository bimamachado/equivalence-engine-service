# Workflows operacionais por decisão

Este documento descreve os fluxos operacionais que acontecem após cada decisão do motor: `DEFERIDO`, `INDEFERIDO`, `COMPLEMENTO` e `ANALISE_HUMANA`.

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

## 3) COMPLEMENTO

- Propósito: indicar que a equivalência pode ser obtida mediante complementos (atividades, disciplina(s) curta, entrega de evidências).

- Checklist automático (sistema):
  1. Persistir resultado com `decisao=COMPLEMENTO` e lista de lacunas (`faltantes`).
  2. Gerar plano de complemento automático (se regra de negócio suportar) ou instrução textual padrão indicando o que complementar.
  3. Notificar aluno com passos a cumprir, prazo sugerido e como pedir reavaliação ao completar.
  4. Gerar entrada em workflow de acompanhamento (ex.: `complemento_pending`).

- Ações manuais recomendadas:
  - Se aplicável, coordenador especifica atividades, prazos e critérios de aceitação.
  - Ao receber evidências, reavaliar automaticamente ou manualmente conforme política.

- Template de justificativa (curta):

  COMPLEMENTO: Similaridade suficiente, requer complementos para aprovação automática.

- Template de justificativa (detalhada):

  Decisão: COMPLEMENTO
  Motivo: {motivo_from_engine}
  Score final: {score}/100
  Lacunas identificadas (node ids): {faltantes}
  Recomendação: {descricao_do_complemento} (ex.: cursar módulo X, entregar plano de estudos Y)

Checklist para reavaliação após complemento:
  - Receber comprovante/atividade/documento.
  - Validar se conteúdo cobre os `faltantes` citados.
  - Rodar reavaliação automática; se score agora >= `min_score_deferir` → aprovar.

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
  5. Decidir entre: `DEFERIDO`, `INDEFERIDO` ou `COMPLEMENTO` (pode também solicitar mais informações).
  6. Registrar justificativa detalhada e ações (aprovar, negar, exigir complemento, anexar observações administrativas).

- Template de nota do avaliador (para registrar na aplicação):

  Avaliador: {nome_avaliador}
  Data: {YYYY-MM-DD}
  Decisão: {DEFERIDO|INDEFERIDO|COMPLEMENTO}
  Racional: {texto explicando motivos, com referências a tópicos/trechos da ementa}
  Ações: {ex.: emitir equivalência / exigir complemento X / abrir recurso}

---

Arquivo criado automaticamente: `DOCS/WORKFLOWS.md` — commit e push serão feitos agora.
