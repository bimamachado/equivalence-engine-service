#!/usr/bin/env python3
"""Run a small suite of API smoke tests against /v1/equivalences/evaluate.
Usage: python tests/run_api_tests.py [base_url]
Exits with code 0 if all checks pass, non-zero otherwise.
"""
import json
import sys
import time
from pathlib import Path

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
URL = f"{BASE}/v1/equivalences/evaluate"

EXAMPLE_PATH = Path("tests/request_example.json")


def load_example():
    if not EXAMPLE_PATH.exists():
        print(f"Missing {EXAMPLE_PATH}")
        sys.exit(2)
    return json.loads(EXAMPLE_PATH.read_text())


def post_json(payload):
    try:
        r = requests.post(URL, json=payload, timeout=30)
        return r
    except Exception as e:
        print(f"Request error: {e}")
        return None


def main():
    fails = 0
    example = load_example()

    print("---RUN 1---")
    r = post_json(example)
    if r is None:
        print("No response")
        fails += 1
    else:
        print(r.status_code)
        print(r.text)
        if r.status_code != 200:
            fails += 1

    time.sleep(0.2)
    print("---RUN 2---")
    r = post_json(example)
    if r is None:
        print("No response")
        fails += 1
    else:
        print(r.status_code)
        print(r.text)
        if r.status_code != 200:
            fails += 1

    time.sleep(0.2)
    print("---RUN 3 (invalid body)---")
    r = post_json({})
    if r is None:
        print("No response")
        fails += 1
    else:
        print(r.status_code)
        print(r.text)
        # expect 4xx
        if 200 <= r.status_code < 400:
            fails += 1

    if fails:
        print(f"TESTS FAILED: {fails} failure(s)")
        sys.exit(1)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
