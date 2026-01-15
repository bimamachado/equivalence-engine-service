# Developer Guide

Setup local dev environment

1. Crie e ative o virtualenv

Linux / macOS / WSL:
```bash
python -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instale dependências
```bash
pip install -r requirements.txt
```

3. Copie e edite `.env`
```bash
cp .env.example .env
# editar variáveis locais (DATABASE_URL, REDIS_URL, etc.)
```

4. Aplicar migrations e popular dados dev
```bash
alembic upgrade head
python -m app.seed
```

Rodando a aplicação
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Rodando testes
```bash
pytest -q
```

Formato e lint
- Use `black` e `ruff` (ou as ferramentas que o projeto usa). Encoraje PRs limpos e pequenos.

Como adicionar um mapper
1. Crie arquivo em `app/mapper` implementando `BaseMapper`.
2. Registre no local de resolução (ver `app/mapper/__init__` ou ponto de construção do mapper).
3. Adicione testes unitários em `tests/`.
4. Atualize documentação se necessário.

Como adicionar uma regra de negócio
- Implemente em `app/engine/hard_rules.py` ou em módulos específicos.
- Garanta cobertura por testes unitários e integração se afetar endpoints.

Trabalhando com filas (RQ)
- Enfileire jobs via `app/queue.py` ou endpoints batch.
- Rode worker local para desenvolvimento:
```bash
rq worker -u redis://localhost:6379/0 equivalence
```

Debugging
- Use logs (`app/logging_setup.py`) e `uvicorn` em modo `--reload`.
- Para investigar jobs RQ: `rq info -u redis://localhost:6379/0`.

Contribuição
- Abra PRs pequenos, escreva testes e descreva mudanças no corpo do PR.
