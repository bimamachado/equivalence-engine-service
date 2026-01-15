# Equivalence Engine Service

Resumo rápido de como rodar o projeto localmente.

Requisitos
- Python 3.10+
- Recomenda-se criar um virtual environment (`.venv`).

```markdown
# Equivalence Engine Service

Resumo rápido de como rodar o projeto localmente e usar a API.

Requisitos
- Python 3.10+
- Recomenda-se criar um virtual environment (`.venv`).

Configuração rápida

1. Criar e ativar o virtualenv

WSL / Linux / macOS:
```bash
python -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependências
```bash
pip install -r requirements.txt
```

3. Criar arquivo de ambiente (copiar o exemplo)
```bash
cp .env.example .env
# editar .env com chaves e endpoints reais
```

4. Rodar a API (exemplo com uvicorn)
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints da API
-----------------

**POST /v1/equivalences/evaluate**

- Descrição: avalia se uma disciplina de origem é equivalente a uma disciplina de destino segundo a `policy` e a `taxonomy_version` informadas.
- Content-Type: `application/json`
- Body: objeto `EvaluateRequest` conforme o schema em `app/api/schemas.py`.

Exemplo de request JSON (mínimo funcional):

```json
{
    "request_id": "req-0001",
    "origem": {
        "nome": "Introdução à Administração",
        "carga_horaria": 60,
        "ementa": "Conceitos básicos de administração, planejamento, missão e visão",
        "aprovado": true,
        "nivel": "basico",
        "ano_conclusao": 2020
    },
    "destino": {
        "nome": "Planejamento Estratégico",
        "carga_horaria": 60,
        "ementa": "Planejamento estratégico, SWOT, objetivos",
        "nivel": "intermediario"
    },
    "policy": {
        "min_score_deferir": 85,
        "min_score_complemento": 70,
        "tolerancia_carga": 1.0,
        "exigir_criticos": true,
        "weights": {"cobertura": 0.6, "critica": 0.4, "nivel": 0.1},
        "confidence_cutoff": 0.5
    },
    "taxonomy_version": "2026.01",
    "policy_version": "1.0",
    "options": {"return_evidence": true, "allow_degraded_fallback": true}
}
```

Nota: a propriedade `tenant_id` não deve ser enviada no corpo da requisição. O serviço resolve o `tenant_id` a partir da chave de API/proxy (por exemplo via header `X-API-Key`) e não confia em valores fornecidos pelo cliente.

Exemplo `curl`:

```bash
curl -sS -X POST http://localhost:8000/v1/equivalences/evaluate \
	-H 'Content-Type: application/json' \
	-d @request.json
```

Exemplo em Python (requests):

```python
import requests
resp = requests.post('http://localhost:8000/v1/equivalences/evaluate', json={
		# payload como o exemplo acima
})
print(resp.status_code)
print(resp.json())
```

Resposta (modelo) — campos principais do `EvaluateResponse`:

- `request_id`: string
- `decisao`: `DEFERIDO` | `INDEFERIDO` | `COMPLEMENTO` | `ANALISE_HUMANA`
- `score`: inteiro 0..100
- `breakdown`: objeto com `cobertura`, `cobertura_critica`, `penalidade_nivel`
- `hard_rules`: lista de resultados das regras duras
- `faltantes`: lista de ids de conceitos faltantes
- `criticos_faltantes`: lista de ids críticos faltantes
- `justificativa_curta` / `justificativa_detalhada`: textos explicativos
- `evidence` (opcional): bloco com `covered_concepts` e listas de faltantes
- `degraded_mode`: bool (se foi usado fallback degradado)
- `model_version`, `policy_version`, `taxonomy_version`, `timings_ms`, `meta`

Exemplo de resposta (parcial):

```json
{
	"request_id": "req-0001",
	"decisao": "COMPLEMENTO",
	"score": 74,
	"breakdown": {"cobertura": 0.6, "cobertura_critica": 1.0, "penalidade_nivel": 0.0},
	"hard_rules": [{"rule": "input_minimo", "ok": true}, ...],
	"faltantes": [1001, 1012],
	"criticos_faltantes": [],
	"justificativa_curta": "Similaridade suficiente, recomenda-se complemento.",
	"justificativa_detalhada": "...",
	"evidence": {"covered_concepts": [...], "missing_concepts": [...], "missing_critical_concepts": [...]},
	"degraded_mode": false,
	"model_version": "mapper-stub-keywords-0.1",
	"policy_version": "1.0",
	"taxonomy_version": "2026.01",
	"timings_ms": {"validate": 1, "map": 50, "score": 4, "total": 60},
	"meta": {"origin_vec_size": 12, "dest_vec_size": 8}
}
```

Observações sobre uso
---------------------

- Autenticação: não há mecanismo de autenticação implementado por padrão — em produção adicione OAuth/API keys/proxy.
- Timeouts: o mapeamento pode chamar clientes externos (embeddings/LLM) configuráveis via variáveis de ambiente `EMBED_URL`, `LLM_URL` etc.; ajuste timeouts e monitoramento.
- Cache: o engine usa `SimpleTTLCache` por padrão; chaves de cache dependem de `tenant_id`, `taxonomy_version` e `ementa`.
- Modo degradado: se o mapper principal falhar em retornar mapeamentos e `options.allow_degraded_fallback` for true, o `fallback_mapper` pode ser usado; o engine marca `degraded_mode` e normalmente exige revisão humana (`ANALISE_HUMANA`).

Arquitetura (resumido)
- `app/engine` — núcleo do motor de equivalência
- `app/mapper` — mappers (stubs, embedding+LLM)
- `app/taxonomy` — modelos e armazenamento da taxonomia
- `app/api` — rotas e schemas

Rodando com Docker / docker-compose
---------------------------------

1) Copie `env` e edite variáveis:

```bash
cp .env.example .env
# editar .env conforme necessário
```

2) Build e up com Docker Compose (inicia web + mock embed + mock llm):

```bash
docker compose build --pull
docker compose up
```

3) A API ficará acessível em `http://localhost:8000` e o mock de embeddings em `http://localhost:9001`.

Notas:
- O `Dockerfile` usa `python:3.10-slim` (multi-arch). Em Apple Silicon o Docker Desktop fará o pull da imagem adequada. Se houver erros de pacotes nativos, instale dependências na imagem ou use imagens com as bibliotecas já presentes.
- Para rodar apenas o serviço web e conectar a endpoints externos (em vez dos mocks), rode:

```bash
docker compose up --no-deps web
```

```

