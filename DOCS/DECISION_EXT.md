# Taxonomia e Versões — Extensão do DECISION.md

Este documento complementa `DOCS/DECISION.md` com definições operacionais e recomendações para os campos relacionados à taxonomia e versões usados pelo pipeline de decisão.

## Taxonomia
- **O que é:** a taxonomia é o conjunto canônico de categorias, rótulos e atributos utilizados para mapear entradas (documentos, produtos, categorias) para termos padronizados que o motor de decisão entende.
- **Para que serve:**
  - Normalizar entrada heterogênea antes de aplicar regras ou cálculo de similaridade.
  - Suportar regras hard-coded que operam sobre categorias conhecidas.
  - Permitir indexação e busca semântica baseada em rótulos estáveis.
- **Onde vive no código:** arquivos e módulos relacionados incluem `app/taxonomy/store.py`, `app/mapper/*` e `app/engine/*` (mapeamento e resolvers).
- **Implicações de mudança:** atualizar a taxonomia pode exigir reindexação, re-treino ou reprocessamento de entradas históricas para manter consistência.
- **Boas práticas:** versionar a taxonomia (ver `taxonomy_version` no exemplo) e manter changelog com mapeamentos antigos → novos.

## `taxonomy_version`
- Identifica a versão do conjunto de categorias/labels utilizado para esse processamento.
- Deve ser um identificador legível (ex.: `2025-11-01`, `tax-v2`).
- Deve acompanhar registros de decisão e auditoria para permitir reavaliação posterior caso a taxonomia mude.

## `version` (campo genérico de esquema)
- Refere-se à versão do esquema do payload/registro de decisão (input/output schema).
- Usado por parsers e validadores para manter compatibilidade ascendente/retroativa.
- Exemplos: `v1`, `v2`, `2025-01-12`.

## `model_version`
- Define explicitamente qual artefato de modelo foi usado durante o mapeamento ou scoring.
  - Para modelos de embedding: pode conter o identificador do provider e versão (ex.: `openai-embed-1.2`).
  - Para modelos LLM: pode indicar prompt-template + modelo (ex.: `gpt-xyz-2025-03:prompt-v3`).
- Importância:
  - Reprodutibilidade: permite reconstruir exatamente as decisões produzidas por um run anterior.
  - Auditoria: essencial para investigar por que um scoring mudou entre execuções.
- Boas práticas:
  - Registrar o `model_version` em cada decisão e em logs de auditoria.
  - Ao atualizar o modelo, criar uma nova `model_version` e testar impacto em um conjunto controlado.

## `policy_version`
- Representa a versão da política de decisão — ou seja, dos parâmetros e thresholds que determinam as faixas para `DEFERIDO`, `ANALISE_HUMANA`, `INDEFERIDO`, etc.
- Exemplos de parâmetros controlados pela `policy_version`:
  - `defer_threshold` (score mínimo para deferir)
  - `complement_threshold` (intervalo que exige complemento)
  - regras hard-coded ativadas/desativadas
- Por que versionar:
  - Mudanças em thresholds alteram comportamentos automaticamente; versionamento ajuda a rastrear e reverter.
  - Deve constar nas evidências de auditoria para cada decisão.

## Exemplo de metadados em payload/registro
```
{
  "version": "v2",
  "taxonomy_version": "tax-v2025-11-01",
  "model_version": "openai-embed-1.2",
  "policy_version": "policy-v3",
  "metadata": { ... }
}
```

## Recomendações operacionais
- Sempre registrar `taxonomy_version`, `model_version` e `policy_version` por decisão para garantir rastreabilidade.
- Antes de promover um novo `policy_version` ou `model_version` para produção, rodar testes A/B e registrar as diferenças em métricas de performance e auditoria.
- Quando a `taxonomy_version` muda de forma incompatível, documentar mapeamentos antigos→novos e considerar reprocessamento de históricos críticos.
- Expor endpoints/rotinas administrativas para listar versões atuais e históricas (útil para suporte e auditoria).

## Onde documentar mudanças
- Registrar mudanças em `DOCS/CHANGELOG.md` e vincular cada alteração de `policy_version`/`model_version`/`taxonomy_version` a um ticket ou release.

---

