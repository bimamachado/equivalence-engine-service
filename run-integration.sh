#!/usr/bin/env bash
set -euo pipefail

# run-integration.sh
# Automated helper to start infra, seed DB and run a sample integration POST.
# Run from WSL/bash: ./run-integration.sh

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Activate or create virtualenv
if [ -f .venv/bin/activate ]; then
  echo "Activating existing virtualenv"
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "Creating virtualenv and installing requirements (may take a while)"
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
fi

# Start infra services (redis/postgres and mocks)
echo "Starting infra (redis, postgres, mocks) via docker compose"
docker compose up -d redis postgres mock-embed mock-llm || docker compose up -d

# Rebuild and (re)start web so it uses local code changes
echo "Building web image and (re)creating web service"
docker compose build --no-cache web || true
docker compose up -d --no-deps --force-recreate web

# Wait for health endpoint
echo -n "Waiting for service to become healthy"
for i in {1..60}; do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo " -> healthy"
    break
  fi
  echo -n '.'
  sleep 1
done

# Seed DB (safe)
echo "Running seed_safe.py"
python scripts/seed_safe.py || true

# Prepare payload
cat > /tmp/integration_payload.json <<'JSON'
{
  "request_id": "run-integ-$(date +%s)",
  "origem": {
    "nome": "Disciplina A",
    "carga_horaria": 60,
    "ementa": "Curso sobre swot, missão e visão",
    "nivel": "basico",
    "ano_conclusao": 2020
  },
  "destino": {
    "nome": "Planejamento Estratégico",
    "carga_horaria": 60,
    "ementa": "Modelos e ferramentas de planejamento estratégico",
    "nivel": "intermediario"
  },
  "taxonomy_version": "2026.01",
  "policy_version": "v3"
}
JSON

# Perform request
echo "POST /v1/equivalences/evaluate ->"
HTTP_STATUS=$(curl -sS -w "%{http_code}" -o /tmp/integration_response.json -X POST http://localhost:8000/v1/equivalences/evaluate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-client-abc123" \
  --data-binary @/tmp/integration_payload.json)

echo "HTTP status: $HTTP_STATUS"

echo "Response body:"
cat /tmp/integration_response.json || true

if [[ "$HTTP_STATUS" =~ ^5 ]]; then
  echo "Server error detected; showing last 200 lines of web logs"
  docker compose logs --no-color --tail=200 web || true
fi

echo "Done"
