# Design Patterns - Equivalence Engine Service

Este documento cataloga os padrões de design (design patterns) aplicados no projeto `equivalence-engine-service`, explicando sua localização, propósito e benefícios.

---

## 📋 Índice

1. [Padrões Arquiteturais](#padrões-arquiteturais)
2. [Padrões Criacionais](#padrões-criacionais)
3. [Padrões Estruturais](#padrões-estruturais)
4. [Padrões Comportamentais](#padrões-comportamentais)
5. [Padrões de Persistência](#padrões-de-persistência)
6. [Padrões de Integração](#padrões-de-integração)

---

## Padrões Arquiteturais

### 1. **Layered Architecture (Arquitetura em Camadas)**

**Localização:** Estrutura geral do projeto

**Descrição:** O projeto está organizado em camadas distintas, cada uma com responsabilidades específicas:

```
├── API Layer (api/, routes)       → Interface HTTP, validação de entrada
├── Service Layer (engine/service) → Lógica de negócio, orquestração
├── Domain Layer (engine/)         → Regras de negócio, decisões
├── Repository Layer (repos.py)    → Acesso a dados, abstraindo persistência
├── Infrastructure Layer (db.py)   → Configuração técnica (DB, Redis, etc.)
```

**Benefícios:**
- ✅ Separação clara de responsabilidades (SRP)
- ✅ Facilita testes unitários (mock de camadas)
- ✅ Manutenibilidade e escalabilidade

**Exemplo:**
```python
# API Layer
@router.post("/v1/equivalences/evaluate")
async def evaluate_equivalence(req: EvaluateRequest, ...):
    return engine.evaluate(req, tenant_id)

# Service Layer (engine/service.py)
class EquivalenceEngine:
    def evaluate(self, req: EvaluateRequest, tenant_id: str):
        # Orquestra: validação → regras → scoring → decisão
        ...

# Repository Layer (repos.py)
class ResultRepo:
    def save_result(self, db: Session, r: EquivalenceResult):
        db.add(r)
        db.commit()
```

---

### 2. **Microservices Pattern (Serviços Independentes)**

**Localização:** `docker-compose.yml`, serviços mock (`mock-embed`, `mock-llm`)

**Descrição:** Serviços especializados e independentes comunicam-se via HTTP:
- **Web API** (FastAPI) - serviço principal
- **Worker** (RQ) - processamento assíncrono
- **Mock Embed** - serviço de embeddings (stub)
- **Mock LLM** - serviço de LLM (stub)

**Benefícios:**
- ✅ Escalabilidade independente de cada serviço
- ✅ Deploy e desenvolvimento isolados
- ✅ Tecnologias heterogêneas (Python, mocks HTTP)

---

## Padrões Criacionais

### 3. **Dependency Injection (Injeção de Dependências)**

**Localização:** `deps.py`, uso do FastAPI Depends

**Descrição:** Dependências são injetadas via parâmetros de função, controladas centralmente.

```python
# deps.py
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_engine(db: Session = Depends(get_db)) -> EquivalenceEngine:
    taxonomy_store = TaxonomyStore(db)
    mapper = TaxonomyMapper(...)
    cache = SimpleTTLCache(...)
    return EquivalenceEngine(taxonomy_store, mapper, ..., cache, ...)

# routes.py
@router.post("/evaluate")
def evaluate(req: EvaluateRequest, engine: EquivalenceEngine = Depends(get_engine)):
    return engine.evaluate(req, ...)
```

**Benefícios:**
- ✅ Testabilidade (mock fácil de dependências)
- ✅ Inversão de controle (IoC)
- ✅ Reduz acoplamento

---

### 4. **Factory Pattern (Fábrica)**

**Localização:** `bootstrap.py`, `deps.py`

**Descrição:** Criação centralizada de objetos complexos (engine, mappers, clientes).

```python
# bootstrap.py
def bootstrap_engine(db: Session, tenant_id: str, course_id: str):
    # Factory para criar EquivalenceEngine com todas dependências
    binding = PolicyRepo().resolve_binding(db, tenant_id, course_id)
    taxonomy_store = TaxonomyStore(db, tenant_id, binding.taxonomy_version_id)
    mapper = create_mapper(...)  # Factory de mapper
    fallback_mapper = create_fallback_mapper(...)
    cache = SimpleTTLCache(ttl=3600)
    audit_repo = AuditRepository(db)
    
    return EquivalenceEngine(taxonomy_store, mapper, fallback_mapper, cache, audit_repo)
```

**Benefícios:**
- ✅ Encapsula lógica de criação complexa
- ✅ Flexibilidade para trocar implementações

---

### 5. **Builder Pattern (Construtor)**

**Localização:** `index_builder.py`, `engine/scoring.py`

**Descrição:** Construção passo-a-passo de objetos complexos.

```python
# index_builder.py
def build_taxonomy_index(tenant_id: str, taxonomy_version: str):
    # 1. Buscar taxonomia
    nodes = fetch_nodes(...)
    
    # 2. Gerar textos
    texts = [build_taxonomy_text(n) for n in nodes]
    
    # 3. Gerar embeddings
    vectors = embedder.embed(texts)
    
    # 4. Persistir índice
    save_embeddings(vectors)
    
    return {"ok": True, "count": len(nodes)}

# engine/scoring.py - build_vector()
def build_vector(matched_concepts, all_nodes):
    vec = [0] * len(all_nodes)
    for c in matched_concepts:
        vec[node_idx(c)] = 1
    return vec
```

**Benefícios:**
- ✅ Construção clara e legível
- ✅ Validação em cada etapa

---

## Padrões Estruturais

### 6. **Repository Pattern (Repositório)**

**Localização:** `repos.py`, `audit/repository.py`, `embedding_repo.py`

**Descrição:** Abstrai operações de persistência, isolando a camada de negócio da infraestrutura.

```python
# repos.py
class TaxonomyRepo:
    def get_nodes(self, db: Session, tenant_id: str, version: str):
        # Lógica SQL abstraída
        ...

class PolicyRepo:
    def get_policy(self, db: Session, tenant_id: str, version: str):
        ...

class ResultRepo:
    def save_result(self, db: Session, r: EquivalenceResult):
        db.add(r)
        db.commit()
```

**Benefícios:**
- ✅ Testabilidade (mock de repos)
- ✅ Troca de banco de dados facilitada
- ✅ DRY (código de acesso centralizado)

---

### 7. **Adapter Pattern (Adaptador)**

**Localização:** `mapper/`, `tools/embed_stub.py`

**Descrição:** Adapta interfaces externas para o formato esperado internamente.

```python
# mapper/base.py
class TaxonomyMapper:
    """Adapta conceitos externos para taxonomia interna"""
    def map(self, origin_text: str) -> list[ConceptMatch]:
        # Transforma texto → conceitos taxonomia
        ...

# tools/embed_stub.py
"""Adapta API de embeddings externa (stub HTTP)"""
@app.post("/embed")
def embed(...):
    # Interface HTTP → lista de vetores
    return {"embeddings": [...]}
```

**Benefícios:**
- ✅ Desacopla serviços externos
- ✅ Facilita mocks e testes

---

### 8. **Facade Pattern (Fachada)**

**Localização:** `engine/service.py` (EquivalenceEngine)

**Descrição:** Interface simplificada para subsistemas complexos.

```python
# engine/service.py
class EquivalenceEngine:
    """Fachada que orquestra: validação, hard rules, scoring, decisão, justificativa"""
    
    def evaluate(self, req: EvaluateRequest, tenant_id: str) -> EvaluateResponse:
        # 1. Validar
        nodes = self.taxonomy_store.get_nodes(...)
        
        # 2. Hard rules
        hard_rules = apply_hard_rules(...)
        
        # 3. Scoring
        score = final_score(...)
        
        # 4. Decisão
        decisao = decide(score, policy, ...)
        
        # 5. Justificativa
        justificativa = build_justification(...)
        
        return EvaluateResponse(decisao, score, justificativa, ...)
```

**Benefícios:**
- ✅ API simples para cliente (1 método)
- ✅ Encapsula complexidade interna

---

### 9. **Decorator Pattern (Decorador)**

**Localização:** `middlewares.py`, `middlewares_obs.py`, `middlewares_rate.py`

**Descrição:** Adiciona funcionalidades dinamicamente (autenticação, observabilidade, rate limiting).

```python
# middlewares.py
class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Decorador que valida API key antes de chamar rota
        api_key = request.headers.get("X-API-Key")
        if not validate_api_key(api_key):
            return JSONResponse({"error": "Unauthorized"}, 401)
        return await call_next(request)

# middlewares_obs.py
class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Decorador que adiciona logs/métricas
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        log_request(request, response, duration)
        return response
```

**Benefícios:**
- ✅ Adiciona comportamento sem modificar código base
- ✅ Composição de funcionalidades (stack de middlewares)

---

## Padrões Comportamentais

### 10. **Strategy Pattern (Estratégia)**

**Localização:** `engine/decision.py`, `mapper/`

**Descrição:** Algoritmos intercambiáveis (diferentes estratégias de decisão/mapeamento).

```python
# engine/decision.py
def decide(score: float, policy: dict, hard_rules: dict) -> str:
    """Estratégia de decisão baseada em política"""
    if hard_rules.get("blocked"):
        return "INDEFERIDO"
    
    if score >= policy["min_score_deferir"]:
        return "DEFERIDO"
    elif score >= policy["min_score_analise"]:
        return "ANALISE_HUMANA"
    else:
        return "INDEFERIDO"

# mapper/ - diferentes estratégias de mapeamento
class SemanticMapper(TaxonomyMapper):
    """Estratégia: mapeamento por similaridade semântica"""
    ...

class KeywordMapper(TaxonomyMapper):
    """Estratégia: mapeamento por palavras-chave"""
    ...
```

**Benefícios:**
- ✅ Facilita A/B testing de algoritmos
- ✅ OCP (Open/Closed Principle)

---

### 11. **Observer Pattern (Observador)**

**Localização:** `rq_hooks.py`, `audit/repository.py`

**Descrição:** Notificação automática de eventos (hooks de jobs, auditoria).

```python
# rq_hooks.py
def on_success(job, connection, result, *args, **kwargs):
    """Observer: executado quando job completa com sucesso"""
    log.info(f"Job {job.id} completed")
    # Atualizar métricas, notificar sistema, etc.

def on_failure(job, connection, type, value, traceback):
    """Observer: executado quando job falha"""
    log.error(f"Job {job.id} failed: {value}")
    # Enviar alerta, registrar erro, etc.

# audit/repository.py
class AuditRepository:
    def log_event(self, event_type: str, data: dict):
        """Observer que registra todos eventos do sistema"""
        self.db.add(AuditLog(event_type=event_type, data=data, ...))
```

**Benefícios:**
- ✅ Desacopla lógica de notificação
- ✅ Extensível (adicionar novos observers)

---

### 12. **Command Pattern (Comando)**

**Localização:** `worker.py`, `queue.py`

**Descrição:** Encapsula requisições como objetos (jobs assíncronos).

```python
# queue.py
def enqueue_batch_job(job_id: str, items: list):
    """Command: encapsula processamento em lote como job"""
    q = Queue(connection=redis_conn)
    q.enqueue(
        process_batch_job,  # Comando
        job_id=job_id,
        items=items,
        timeout=3600
    )

# worker.py
def process_batch_job(job_id: str, items: list):
    """Executor do comando"""
    for item in items:
        process_item(item)
    update_job_status(job_id, "DONE")
```

**Benefícios:**
- ✅ Processamento assíncrono
- ✅ Retry, timeout, scheduling

---

### 13. **Template Method Pattern (Método Template)**

**Localização:** `engine/service.py` (evaluate), `scripts/entrypoint.sh`

**Descrição:** Define o esqueleto de um algoritmo, delegando etapas específicas.

```python
# engine/service.py
class EquivalenceEngine:
    def evaluate(self, req: EvaluateRequest, tenant_id: str):
        """Template method: define fluxo geral"""
        # 1. Validar (extensível)
        self._validate(req)
        
        # 2. Hard rules (extensível)
        hard_rules = self._apply_hard_rules(req)
        
        # 3. Scoring (extensível)
        score = self._calculate_score(req)
        
        # 4. Decisão (extensível)
        decisao = self._decide(score, hard_rules)
        
        # 5. Justificativa (extensível)
        justificativa = self._build_justification(...)
        
        return EvaluateResponse(...)
    
    def _validate(self, req):
        """Hook point: pode ser sobrescrito"""
        ...
```

**Benefícios:**
- ✅ Padroniza fluxo de execução
- ✅ Permite customização de etapas

---

## Padrões de Persistência

### 14. **Unit of Work (Unidade de Trabalho)**

**Localização:** `deps.py` (get_db), transações SQLAlchemy

**Descrição:** Agrupa operações de banco em uma transação atômica.

```python
# deps.py
def get_db():
    db = SessionLocal()
    try:
        yield db  # Unit of Work ativo
        # Commit implícito ao final (se sucesso)
    except Exception:
        db.rollback()  # Rollback em caso de erro
        raise
    finally:
        db.close()

# Uso em rota
@router.post("/evaluate")
def evaluate(req: EvaluateRequest, db: Session = Depends(get_db)):
    # Todas operações no mesmo UoW
    result = engine.evaluate(req, ...)
    result_repo.save_result(db, result)
    audit_repo.log(db, "evaluate", ...)
    # Commit automático ao fim da requisição
```

**Benefícios:**
- ✅ Consistência transacional
- ✅ Rollback automático em erros

---

### 15. **Identity Map (Mapa de Identidade)**

**Localização:** SQLAlchemy Session (nativo)

**Descrição:** Cache de primeira camada, evita queries duplicadas na mesma sessão.

```python
# SQLAlchemy Identity Map (automático)
db = Session()
obj1 = db.get(Model, id=1)  # Query no banco
obj2 = db.get(Model, id=1)  # Retorna from cache
assert obj1 is obj2  # Mesma instância (identidade)
```

**Benefícios:**
- ✅ Performance (reduz queries)
- ✅ Consistência de identidade

---

### 16. **Lazy Loading (Carregamento Preguiçoso)**

**Localização:** SQLAlchemy relationships

**Descrição:** Dados relacionados são carregados sob demanda.

```python
# models.py
class CourseBinding(Base):
    taxonomy_version = relationship("TaxonomyVersion", lazy="select")
    # Carregado apenas quando acessado

# Uso
binding = db.get(CourseBinding, id)
# taxonomy_version ainda não carregado (lazy)
version = binding.taxonomy_version  # Query executada agora
```

**Benefícios:**
- ✅ Performance inicial (menos joins)
- ⚠️ Cuidado com N+1 queries

---

## Padrões de Integração

### 17. **Circuit Breaker (Disjuntor)**

**Localização:** `mapper/clients.py` (implícito em retry logic)

**Descrição:** Previne chamadas repetidas a serviços externos falhando.

```python
# mapper/clients.py (conceitual)
class SimpleHttpEmbeddingClient:
    def __init__(self, ...):
        self.failures = 0
        self.circuit_open = False
    
    def embed(self, texts: list[str]):
        if self.circuit_open:
            raise ServiceUnavailable("Circuit breaker open")
        
        try:
            response = requests.post(...)
            self.failures = 0  # Reset em sucesso
            return response.json()
        except Exception as e:
            self.failures += 1
            if self.failures >= 3:
                self.circuit_open = True  # Abre circuito
            raise
```

**Benefícios:**
- ✅ Resiliência a falhas de serviços externos
- ✅ Fail-fast (evita timeouts em cascata)

---

### 18. **Retry Pattern (Tentativa Repetida)**

**Localização:** `worker.py` (RQ retry), `mapper/clients.py`

**Descrição:** Tenta operação novamente em caso de falha temporária.

```python
# worker.py (RQ built-in)
@job('default', retry=Retry(max=3, interval=[10, 30, 60]))
def process_item(item_id):
    # Retry automático: 3 tentativas com backoff
    ...

# mapper/clients.py (HTTP retry)
def call_external_api(url, retries=3):
    for attempt in range(retries):
        try:
            return requests.post(url, ...)
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

**Benefícios:**
- ✅ Handle falhas transitórias (rede, timeout)
- ✅ Aumenta disponibilidade

---

### 19. **Cache-Aside Pattern (Cache Lateral)**

**Localização:** `cache/cache.py`, `engine/service.py`

**Descrição:** Aplicação gerencia cache explicitamente (read-through, write-around).

```python
# cache/cache.py
class SimpleTTLCache:
    def get_or_compute(self, key: str, compute_fn, ttl: int):
        # 1. Tenta buscar no cache
        if key in self.cache:
            return self.cache[key]
        
        # 2. Se não existe, computa
        value = compute_fn()
        
        # 3. Armazena no cache
        self.cache[key] = (value, time.time() + ttl)
        return value

# engine/service.py
score = cache.get_or_compute(
    f"score:{req.hash()}",
    lambda: compute_score(req),
    ttl=3600
)
```

**Benefícios:**
- ✅ Reduz latência e carga no banco
- ✅ Controle explícito de invalidação

---

### 20. **Idempotency Pattern (Idempotência)**

**Localização:** `repos_idempotency.py`, `api/batch_routes.py`

**Descrição:** Operação pode ser repetida sem efeitos colaterais duplicados.

```python
# repos_idempotency.py
class IdempotencyRepo:
    def is_duplicate(self, request_id: str):
        return self.db.query(IdempotencyKey).filter_by(key=request_id).first() is not None
    
    def mark_processed(self, request_id: str, result: dict):
        self.db.add(IdempotencyKey(key=request_id, result=result))
        self.db.commit()

# api/batch_routes.py
@router.post("/batch")
def create_batch(req: BatchRequest, idempotency_key: str = Header(None)):
    if idempotency_repo.is_duplicate(idempotency_key):
        return idempotency_repo.get_result(idempotency_key)  # Retorna resultado anterior
    
    # Processa requisição
    result = process_batch(req)
    idempotency_repo.mark_processed(idempotency_key, result)
    return result
```

**Benefícios:**
- ✅ Seguro para retry (evita duplicação)
- ✅ Essencial em operações críticas (pagamento, equivalência)

---

## 📊 Resumo por Categoria

| Categoria | Padrões Identificados | Benefício Principal |
|-----------|----------------------|---------------------|
| **Arquitetura** | Layered, Microservices | Separação de responsabilidades |
| **Criação** | DI, Factory, Builder | Flexibilidade e testabilidade |
| **Estrutura** | Repository, Adapter, Facade, Decorator | Desacoplamento |
| **Comportamento** | Strategy, Observer, Command, Template Method | Extensibilidade |
| **Persistência** | Unit of Work, Identity Map, Lazy Loading | Consistência e performance |
| **Integração** | Circuit Breaker, Retry, Cache-Aside, Idempotency | Resiliência |

---

## 🎯 Próximos Padrões Recomendados

1. **CQRS (Command Query Responsibility Segregation)**: Separar leitura e escrita para otimizar queries complexas
2. **Event Sourcing**: Armazenar histórico completo de eventos (auditoria avançada)
3. **Saga Pattern**: Transações distribuídas entre microserviços
4. **Feature Flags**: Toggle de funcionalidades sem deploy
5. **Anti-Corruption Layer**: Proteger domínio de mudanças em APIs externas

---

## 📚 Referências

- **Gang of Four (GoF)**: Design Patterns: Elements of Reusable Object-Oriented Software
- **Martin Fowler**: Patterns of Enterprise Application Architecture
- **Microsoft**: Cloud Design Patterns (Azure Architecture Center)
- **FastAPI Docs**: Dependency Injection, Middleware
- **SQLAlchemy Docs**: ORM Patterns, Session Management

---

**Última atualização:** 16/02/2026  
**Versão:** 1.0  
**Autores:** Equipe Equivalence Engine
