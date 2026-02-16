# README-FIRST — Ordem de Leitura Recomendada

Este arquivo indica, **em ordem lógica**, quais documentos ler para entender, configurar e operar o projeto **Equivalence Engine Service**.

---

## 📖 Ordem de Leitura

### 1️⃣ Visão Geral e Contexto

**Comece aqui para entender O QUE o sistema faz e POR QUÊ.**

1. [DOCS/README.md](DOCS/README.md) → Visão geral e instruções rápidas
2. [DOCS/equivalence-engine.md](DOCS/equivalence-engine.md) → Filosofia e objetivos do motor
3. [docs/TECNOLOGIAS.md](docs/TECNOLOGIAS.md) → Stack técnico (Python, FastAPI, PostgreSQL, Redis, RQ)

---

### 2️⃣ Arquitetura do Sistema

**Entenda COMO o sistema funciona internamente.**

4. [DOCS/MACRO_TO_MICRO.md](DOCS/MACRO_TO_MICRO.md) → Separação de responsabilidades entre componentes
5. [DOCS/WORKFLOWS.md](DOCS/WORKFLOWS.md) → Fluxo de avaliação e decisões
6. [DOCS/DECISION.md](DOCS/DECISION.md) → Lógica de decisão (DEFERIDO, INDEFERIDO, ANALISE_HUMANA)
7. [DOCS/ARCHITECTURE/architecture_diagram.md](DOCS/ARCHITECTURE/architecture_diagram.md) → Diagrama de arquitetura
8. [DOCS/DESIGN_PATTERNS.md](DOCS/DESIGN_PATTERNS.md) → **⭐ Design patterns aplicados (Repository, DI, Strategy, etc.)**

---

### 3️⃣ Setup e Configuração Local

**Aprenda a RODAR o projeto localmente.**

9. [docs/operations/dev_run.md](docs/operations/dev_run.md) → **⭐ LEIA PRIMEIRO** runbook completo de desenvolvimento
10. [docker-compose.yml](docker-compose.yml) → Compose com todos os serviços
11. [.env.example](.env.example) ou [prod.env.example](prod.env.example) → Variáveis de ambiente necessárias

**Passos essenciais:**
```bash
# 1. Criar .env baseado em prod.env.example
# 2. Subir stack
docker compose up -d

# 3. Rodar migrations (se necessário)
alembic upgrade head

# 4. Popular dados de exemplo (API keys)
python -m app.seed

# 5. Testar API
curl -sS http://localhost:8000/health
```

---

### 4️⃣ Uso da API

**Conheça os ENDPOINTS e como consumir.**

12. [DOCS/USAGE.md](DOCS/USAGE.md) → Guia de uso da API
13. [DOCS/API_EXAMPLES.md](DOCS/API_EXAMPLES.md) → Exemplos de chamadas (curl e Python)
14. [docs/SMOKE_TEST.md](docs/SMOKE_TEST.md) → Como validar o sistema com smoke tests

---

### 5️⃣ Operações e Troubleshooting

**Monitore e resolva problemas.**

15. [DOCS/RUNBOOK.md](DOCS/RUNBOOK.md) → Runbook operacional
16. [docs/operations/cheatsheet.md](docs/operations/cheatsheet.md) → Comandos rápidos e URLs
17. [docs/runbooks/operations.md](docs/runbooks/operations.md) → Procedimentos operacionais
18. [docs/runbooks/incident_response.md](docs/runbooks/incident_response.md) → Resposta a incidentes

---

### 6️⃣ Deploy e Produção

**Suba em ambiente de produção.**

19. [DOCS/README.deploy.md](DOCS/README.deploy.md) → Checklist e instruções de deploy
20. [docs/deploy.md](docs/deploy.md) → Guia detalhado de deploy
21. [DOCS/SECURITY.md](DOCS/SECURITY.md) → Segurança e gestão de segredos

---

### 7️⃣ Desenvolvimento e Extensão

**Adicione novos recursos ao sistema.**

22. [DOCS/DEVELOPER.md](DOCS/DEVELOPER.md) → Guia de desenvolvimento
23. [DOCS/DESIGN_PATTERNS.md](DOCS/DESIGN_PATTERNS.md) → Padrões de design implementados
24. [docs/SCRIPTS_GUIDE.md](docs/SCRIPTS_GUIDE.md) → Explicação de cada script na pasta `scripts/`
25. [DOCS/CONTRIBUTING.md](DOCS/CONTRIBUTING.md) → Orientações para contribuir

---

## 🚀 Quick Start (5 minutos)

Se você quer apenas **ver o sistema funcionando**:

```bash
# 1. Clone e entre no diretório
cd equivalence-engine-service

# 2. Criar .env
cp prod.env.example .env
# Ajuste DATABASE_URL, REDIS_URL, API_KEY_SALT conforme necessário

# 3. Subir stack
docker compose up -d

# 4. Aguardar health (~15s)
curl -sS http://localhost:8000/health

# 5. Popular API keys (dev)
python -m app.seed

# 6. Testar avaliação
curl -sS -X POST http://localhost:8000/v1/equivalences/evaluate \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-admin-abc123' \
  -d '{"request_id":"req-001","origem":{"nome":"Algoritmos","carga_horaria":60,"ementa":"...","aprovado":true,"nivel":"intermediario"},"destino":{"nome":"Introdução a Programação","carga_horaria":60,"ementa":"...","nivel":"basico"},"policy":{"min_score_deferir":85},"taxonomy_version":"2026.01"}'
```

---

## 📚 Estrutura de Pastas

```
equivalence-engine-service/
├── app/                 # Código da aplicação
│   ├── api/             # Rotas e schemas
│   ├── engine/          # Motor de decisão
│   ├── mapper/          # Mappers (embeddings, LLM)
│   └── tools/           # Stubs (embed, llm)
├── DOCS/                # Documentação principal
│   ├── README.md
│   ├── DEVELOPER.md
│   ├── RUNBOOK.md
│   └── ...
├── docs/                # Documentação operacional (espelhada do DVP)
│   ├── operations/      # Runbooks e cheatsheets
│   ├── runbooks/        # Procedimentos de incidente
│   └── ...
├── scripts/             # Scripts de automação
├── tests/               # Testes
├── alembic/             # Migrations
└── docker-compose.yml
```

---

## 📚 Documentos por Finalidade

### Para Iniciantes
1. [DOCS/README.md](DOCS/README.md) - O que é o sistema
2. [docs/TECNOLOGIAS.md](docs/TECNOLOGIAS.md) - Stack técnico
3. [docs/operations/dev_run.md](docs/operations/dev_run.md) - Como rodar localmente
4. [docs/SMOKE_TEST.md](docs/SMOKE_TEST.md) - Como testar

### Para Desenvolvedores
1. [DESIGN_PATTERNS.md](DESIGN_PATTERNS.md) - Padrões de design aplicados
3. [docs/SCRIPTS_GUIDE.md](docs/SCRIPTS_GUIDE.md) - Scripts disponíveis
4. [docs/SCRIPTS_GUIDE.md](docs/SCRIPTS_GUIDE.md) - Scripts disponíveis
3. [DOCS/WORKFLOWS.md](DOCS/WORKFLOWS.md) - Fluxo de avaliação

### Para Operações
1. [docs/operations/cheatsheet.md](docs/operations/cheatsheet.md) - Comandos rápidos
2. [docs/runbooks/operations.md](docs/runbooks/operations.md) - Procedimentos operacionais
3. [DOCS/RUNBOOK.md](DOCS/RUNBOOK.md) - Troubleshooting

### Para Product/Business
1. [DOCS/equivalence-engine.md](DOCS/equivalence-engine.md) - Casos de uso
2. [DOCS/USAGE.md](DOCS/USAGE.md) - Como consumir a API

---

**Última atualização:** 2026-02-13  
**Mantenedor:** Equipe Equivalence Engine
