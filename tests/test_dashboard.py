import os
import requests
import pytest


@pytest.mark.integration
def test_dashboard_access():
    if os.getenv("RUN_INTEGRATION", "0") != "1":
        pytest.skip("Set RUN_INTEGRATION=1 to run integration tests")

    base = os.environ.get("BASE_URL", "http://localhost:8000")
    headers = {"X-API-Key": os.environ.get("ADMIN_API_KEY", "dev-admin-abc123")}

    r = requests.get(f"{base}/dashboard", headers=headers, timeout=10)
    assert r.status_code == 200
    assert ("Resultados" in r.text) or ("Auditoria" in r.text) or ("Resultados (últimos" in r.text)
