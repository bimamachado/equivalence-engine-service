## Diagrama Arquitetural — Equivalence Engine Service

Copie o bloco abaixo para um visualizador Mermaid (ou use em slides que suportem Mermaid).

```mermaid
flowchart LR
  subgraph EAD[Instituição / EAD]
    A[Sistema Acadêmico] -->|Enviar pares (origem→destino)| API_GW[API (FastAPI)]
  end

  subgraph Service[Microserviço de Equivalência]
    API_GW --> Engine[Engine de Equivalência]
    Engine --> EmbeddingSvc[Embeddings (mock-embed / provider)]
    Engine --> Mapper[Mapper / Taxonomia]
    Engine --> Scoring[Scoring & Hard Rules]
    Scoring --> Decision[Decisor (política)]
    Decision --> ResultStore[(Postgres: EquivalenceResult, Job, JobItem)]
    Engine -->|escrever logs/metrics| Observability[Metrics / Logs]
  end

  subgraph Infra[Infra (Docker Compose)]
    Redis[(Redis / RQ)]
    Postgres[(Postgres)]
    MockLLM[(LLM mock / serviço externo)]
  end

  API_GW -->|consulta| Postgres
  Engine -->|usa| Postgres
  Engine -->|usa| Redis
  EmbeddingSvc -->|chama| MockLLM

  subgraph WorkerProc[Worker (RQ)]
    Worker[Worker processando JobItem] -->|consome fila| Redis
    Worker -->|chama Engine (local)| Engine
    Worker --> ResultStore
  end

  % interactions
  API_GW -->|enfileira itens| Redis
  Redis -->|fila:equivalence| Worker

  classDef infra fill:#f3f4f6,stroke:#111,stroke-width:1px;
  class Infra infra

  click EmbeddingSvc "../app/mapper/embedding_llm_mapper.py" "Implementação do mapper/embeddings"
  click Worker "../app/worker.py" "Lógica de processamento em lote"
  click API_GW "../app/api/routes.py" "Endpoints principais"

``` 

Observações rápidas
- O `Engine` é responsável por transformar entrada → vetores (embeddings), calcular cobertura, aplicar regras duras, agregar sinais e produzir `EquivalenceResult`.
- O `Worker` consome itens em background via RQ/Redis e persiste resultados em Postgres; o `test_ui` depende do worker estar ativo e com variáveis de ambiente corretas.
- Componentes de infra (Postgres / Redis / mock services) podem rodar via `docker compose` (temos um `docker-compose.yml` no repositório).

Arquivo fonte: DOCS/ARCHITECTURE/architecture_diagram.md
