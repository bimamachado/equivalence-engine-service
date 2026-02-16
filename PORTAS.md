# Esquema de Portas - Equivalence Engine Service

Para evitar conflitos com `document-validation-platform`, todas as portas externas foram alteradas.

## Mapeamento de Portas (Host → Container)

| Serviço       | Porta Host | Porta Container | URL de Acesso (localhost)         |
|---------------|------------|-----------------|-----------------------------------|
| **web**       | 8100       | 8100            | http://localhost:8100             |
| **mock-embed**| 9101       | 9101            | http://localhost:9101             |
| **mock-llm**  | 9102       | 9102            | http://localhost:9102             |
| **postgres**  | 5433       | 5432            | postgresql://localhost:5433       |
| **redis**     | 6380       | 6379            | redis://localhost:6380            |

## URLs Internas (entre containers)

Os containers se comunicam usando as portas internas do Docker network:

```env
DATABASE_URL=postgresql+psycopg2://equivalence:equivalence@postgres:5432/equivalence
REDIS_URL=redis://redis:6379/0
EMBED_URL=http://mock-embed:9101
LLM_URL=http://mock-llm:9102
```

## Testes Rápidos

```bash
# Health check da API
curl http://localhost:8100/health

# Testar Postgres
psql -h localhost -p 5433 -U equivalence -d equivalence

# Testar Redis
redis-cli -p 6380 ping

# Documentação interativa (Swagger)
open http://localhost:8100/docs
```

## Executar os Serviços

```bash
# Subir todos os serviços
docker compose up -d

# Verificar status
docker compose ps

# Ver logs
docker compose logs -f web

# Parar serviços
docker compose down
```

## Notas

- ✅ **Portas externas** (host) foram alteradas para evitar conflitos
- ✅ **Portas internas** (container) permanecem padrão
- ✅ Serviços independentes podem rodar simultaneamente
- ✅ Todas as documentações foram atualizadas
