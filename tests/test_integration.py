import json
import os
import subprocess
from pathlib import Path
import shutil
import pytest


@pytest.mark.integration
def test_run_integration_script_is_successful(tmp_path):
    """
    Runs the `run-integration.sh` script as an end-to-end smoke test.
    This test is skipped by default unless the `RUN_INTEGRATION` env var is set,
    to avoid running Docker-based integration during normal unit test runs.
    """
    if os.getenv("RUN_INTEGRATION", "0") != "1":
        pytest.skip("Set RUN_INTEGRATION=1 to run integration tests")

    # if docker is not available (e.g. running inside container), skip
    if shutil.which("docker") is None:
        pytest.skip("docker not available; skipping full run-integration script")

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "run-integration.sh"
    assert script.exists(), f"run-integration.sh not found at {script}"

    proc = subprocess.run([str(script)], cwd=str(repo_root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
    out = proc.stdout
    assert proc.returncode == 0, f"run-integration.sh failed (exit {proc.returncode}):\n{out}"

    resp_file = Path("/tmp/integration_response.json")
    assert resp_file.exists(), f"Integration response file not found; script output:\n{out}"

    data = json.loads(resp_file.read_text())
    assert "request_id" in data, f"response missing request_id: {data}"
    assert "decisao" in data or "status" in data, f"response missing decisao/status: {data}"
