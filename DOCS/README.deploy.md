# Deploy / Produção

Este arquivo descreve passos e recomendações para rodar o serviço em produção.

1) Variáveis sensíveis
- Armazene em um secret manager (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, etc.).
- Variáveis críticas: `POSTGRES_PASSWORD`, `DATABASE_URL`, `REDIS_URL`, `API_KEY_SALT`, `EMBED_API_KEY`, `LLM_API_KEY`.

2) Docker Compose (produção)
- `docker-compose.prod.yml` está preparado para usar variáveis de ambiente via `${VAR}`.
- Antes de subir, exporte ou injete as variáveis necessárias no ambiente do host/container orchestration.

Exemplo (Linux):
```bash
export POSTGRES_PASSWORD="<secure>"
export DATABASE_URL="postgresql+psycopg2://equivalence:${POSTGRES_PASSWORD}@postgres:5432/equivalence"
export REDIS_URL="redis://redis:6379/0"
export API_KEY_SALT="$(openssl rand -hex 32)"
# então
docker compose -f docker-compose.prod.yml up -d --build
```

3) Banco de dados
- Use volumes ou PVCs (kubernetes) para persistência do `pgdata`.
- Tenha rotina de backup e restore (pg_dump / base backups). Exemplo básico de backup:
```bash
docker exec -t postgres pg_dumpall -c -U equivalence > dump_$(date +%F).sql
```

4) Migrações
- Rode as migrations do Alembic durante o deploy (antes de iniciar a API):
```bash
alembic upgrade head
```
- Em pipelines CI/CD, execute migrations em step separado com controle de release.

5) Workers
- Workers RQ devem ser dimensionados separadamente (replicas) e conectados ao Redis de produção.
- Compose prod já define serviço de worker (`command: ["rq","worker",...]`).

6) Observabilidade e monitoramento
- Exponha métricas (Prometheus) e configure alertas para:
  - falhas de conexões DB/Redis
  - filas RQ acumulando
  - latência de endpoints críticos
- Centralize logs (ELK/CloudWatch)

7) Segurança
- Rode containers com usuário não-root quando possível.
- Habilite TLS (ingress/load balancer) para tráfego HTTP.
- Proteja endpoints administrativos com autenticação e redes privadas.

8) Rollbacks
- Mantenha estratégia de rollback para migrations e imagens de containers (tagging de imagens).

9) Checklist rápido antes do deploy
- [ ] Segredos em secret manager
- [ ] Backup recente do DB
- [ ] Migrations testadas em staging
- [ ] Workers configurados
- [ ] Monitoramento / alertas ativos

