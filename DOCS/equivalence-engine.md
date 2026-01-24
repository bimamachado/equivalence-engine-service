

---

# 🧠 Equivalence Engine Service

**Motor Inteligente de Equivalência de Disciplinas (EAD / Acadêmico)**

## Visão Geral (Macro)

Este projeto implementa um **microserviço de avaliação automática de equivalência de disciplinas**, projetado para ambientes acadêmicos EAD (e presenciais, se quiserem evoluir).

O objetivo é substituir decisões subjetivas, manuais e inconsistentes por um **motor determinístico, auditável e explicável**, com suporte opcional a **IA (embeddings + LLM)**.

Em resumo, o serviço:

* recebe dados de uma disciplina de origem e uma de destino
* avalia regras acadêmicas objetivas (regras duras)
* compara conteúdos de forma semântica
* calcula scores de equivalência
* aplica políticas institucionais
* retorna uma decisão clara, justificada e rastreável

Sem achismo. Sem “parece equivalente”. Sem planilha mágica.

---

## O Problema que Isso Resolve

Em sistemas acadêmicos tradicionais, equivalência de disciplinas costuma ser:

* manual
* lenta
* inconsistente
* impossível de auditar depois
* dependente de interpretação humana variável

Isso gera:

* retrabalho
* judicialização
* insatisfação de alunos
* gargalos operacionais

Este projeto resolve isso criando um **motor centralizado de decisão**, com:

* critérios explícitos
* versionamento
* rastreabilidade
* explicabilidade

---

## Arquitetura Geral (Macro)

O serviço foi desenhado como um **microserviço independente**, stateless, com as seguintes características:

* API HTTP (FastAPI)
* Engine determinístico (regras + score)
* Mapper semântico plugável (IA opcional)
* Cache agressivo para custo/performance
* Modo degradado quando IA falha
* Auditoria por request

Arquitetura conceitual:

```
Sistema Acadêmico / API Gateway
          |
          v
Equivalence Engine Service
          |
          +--> Regras Duras
          +--> Mapper Semântico (Embeddings / LLM)
          +--> Scoring
          +--> Decision Policy
          +--> Justificativa
          +--> Auditoria
```

A IA **não decide sozinha**. Ela só ajuda a mapear conceitos.
A decisão final é sempre do **motor de regras**.

---

## Filosofia de Projeto (Importante)

Alguns princípios não negociáveis deste projeto:

1. **Determinismo**

   * Mesma entrada + mesmas versões = mesma saída.

2. **Explicabilidade**

   * Toda decisão vem com justificativa e evidências.

3. **Versionamento**

   * Taxonomia, política e modelo sempre versionados.

4. **Fail-safe**

   * Se a IA falhar, o sistema não cai. Entra em modo degradado.

5. **Separação de responsabilidades**

   * Regras ≠ IA ≠ Persistência ≠ API.

6. **Pronto para auditoria**

   * Tudo que decide pode ser explicado depois.

---

## Stack Tecnológica

* **Python 3.11+**
* **FastAPI** (API)
* **Pydantic** (schemas e validação)
* **Embeddings** (via serviço externo ou local)
* **LLM opcional** (refino semântico)
* **Redis / Cache em memória** (MVP)
* **PostgreSQL/MySQL** (opcional, para auditoria em produção)

Nada exótico. Nada experimental demais.

---

## Estrutura do Projeto (Meso)

```
equivalence_service/
│
├── app/
│   ├── api/            # Endpoints HTTP e schemas
│   ├── engine/         # Coração do sistema (regras, score, decisão)
│   ├── mapper/         # Mapeamento semântico (embeddings + LLM)
│   ├── taxonomy/       # Taxonomia acadêmica versionada
│   ├── cache/          # Cache (hash-based)
│   ├── audit/          # Auditoria (MVP ou DB)
│   ├── main.py         # FastAPI bootstrap
│
├── tools/              # Stubs locais (embed/llm)
├── tests/              # Testes unitários
└── README.md
```

---

## Componentes Internos (Micro)

### 1. API (`app/api`)

Responsável apenas por:

* receber requests
* validar dados
* chamar o engine
* devolver resposta

Nenhuma regra de negócio mora aqui.

---

### 2. Engine (`app/engine`)

É o **cérebro** do sistema.

Pipeline interno do `evaluate()`:

1. Validação estrutural
2. Aplicação de regras duras
3. Mapeamento semântico (cacheado)
4. Construção de vetores conceituais
5. Cálculo de cobertura
6. Cálculo de cobertura crítica
7. Penalidade de nível (opcional)
8. Cálculo de score final
9. Aplicação de política de decisão
10. Geração de justificativa
11. Registro de auditoria

Esse pipeline é **determinístico**.

---

### 3. Regras Duras (`hard_rules`)

Regras que **bloqueiam** equivalência independentemente de IA:

Exemplos:

* disciplina não aprovada
* carga horária insuficiente
* validade temporal expirada
* input mínimo ausente

Se falhar aqui, a IA nem é chamada.

---

### 4. Taxonomia (`taxonomy`)

Modelo formal do conhecimento acadêmico.

Cada conceito possui:

* área / subárea
* descrição
* palavras-chave
* nível (básico, intermediário, avançado)
* flag de criticidade

A taxonomia é **versionada**.
Mudar a taxonomia muda o resultado, e isso fica registrado.

---

### 5. Mapper (`mapper`)

Responsável por transformar texto livre (ementa) em **conceitos da taxonomia**.

Estratégia padrão:

1. Embedding da ementa
2. Similaridade com embeddings da taxonomia
3. Seleção Top-K conceitos
4. Conversão para pesos e confiança
5. (Opcional) refinamento via LLM com evidências

O mapper **não decide nada**. Só sugere.

---

### 6. Scoring

Cálculo matemático simples e transparente:

* Cobertura conceitual
* Cobertura de conceitos críticos
* Penalidade por nível
* Pesos configuráveis por política

Resultado final: `score 0–100`

---

### 7. Decision Policy

Transforma score + critérios em decisão:

* `DEFERIDO`
* `ANALISE_HUMANA`
* `INDEFERIDO`
* `ANALISE_HUMANA` (modo degradado)

As regras de decisão são explícitas e configuráveis.

---

### 8. Justificativa

Toda resposta inclui:

* justificativa curta (UI)
* justificativa detalhada (auditoria)
* conceitos faltantes
* conceitos críticos não cobertos
* valores de score

Nada de “indeferido porque sim”.

---

### 9. Cache

* Cache por hash da ementa + versão
* Evita pagar embeddings/LLM repetidamente
* Reduz latência e custo drasticamente

---

### 10. Auditoria

Cada request pode registrar:

* request_id
* versões usadas
* score
* decisão
* timings
* hashes (não o texto completo)

Isso permite:

* defesa institucional
* explicação posterior
* compliance

---

## Modo Degradado (IA falhou? Problema nenhum.)

Se:

* embeddings falham
* LLM não responde
* confiança é insuficiente

O sistema:

* marca `degraded_mode = true`
* evita deferimento automático
* retorna `ANALISE_HUMANA` ou decisão conservadora
* explica isso claramente

O sistema **nunca mente**.

---

## Como Rodar (MVP)

```bash
pip install fastapi uvicorn pydantic
uvicorn app.main:app --reload
```

Health check:

```
GET /health
```

Avaliação:

```
POST /v1/equivalences/evaluate
```

---

## Casos de Uso Suportados

* Equivalência automática
* Sugestão de complemento
* Indeferimento técnico
* Triagem para análise humana
* Lote (futuro)
* Multi-tenant (futuro)

---

## O que este projeto NÃO é

* Não é portal acadêmico
* Não é sistema de matrícula
* Não é workflow administrativo
* Não é substituto de parecer humano quando necessário

Ele é **um motor**. Só isso. E isso já resolve muita coisa.

---

## Próximos Passos Naturais

* Persistência real da taxonomia e políticas
* Worker de batch (fila)
* Index persistente de embeddings
* Dashboard interno de auditoria
* Fine-tuning de thresholds por curso

---
