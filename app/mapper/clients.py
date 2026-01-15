from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, Optional
import json
import time
import urllib.request
import urllib.error


class EmbeddingClient(Protocol):
    def embed(self, texts: List[str]) -> List[List[float]]:
        ...


class LLMJsonClient(Protocol):
    def complete_json(self, system: str, user: str, json_schema: Dict[str, Any]) -> Dict[str, Any]:
        ...


@dataclass
class HttpClientConfig:
    base_url: str
    api_key: Optional[str] = None
    timeout_seconds: int = 15


class SimpleHttpEmbeddingClient:
    """
    Cliente genérico: chama um endpoint HTTP que recebe {texts:[...]} e devolve {vectors:[[...], ...]}.
    Você implementa esse endpoint onde quiser (OpenAI/Azure/local).
    """
    def __init__(self, cfg: HttpClientConfig, path: str = "/embed"):
        self.cfg = cfg
        self.path = path

    def embed(self, texts: List[str]) -> List[List[float]]:
        url = self.cfg.base_url.rstrip("/") + self.path
        payload = json.dumps({"texts": texts}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.cfg.api_key:
            req.add_header("Authorization", f"Bearer {self.cfg.api_key}")

        try:
            with urllib.request.urlopen(req, timeout=self.cfg.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["vectors"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Embedding HTTPError: {e.code} {e.reason}") from e
        except Exception as e:
            raise RuntimeError(f"Embedding error: {e}") from e


class SimpleHttpLLMJsonClient:
    """
    Cliente genérico: chama um endpoint HTTP que recebe:
      {system, user, json_schema} e devolve {json: {...}}
    Ideal para padronizar saída e evitar “texto criativo” inútil.
    """
    def __init__(self, cfg: HttpClientConfig, path: str = "/llm/json"):
        self.cfg = cfg
        self.path = path

    def complete_json(self, system: str, user: str, json_schema: Dict[str, Any]) -> Dict[str, Any]:
        url = self.cfg.base_url.rstrip("/") + self.path
        payload = json.dumps({
            "system": system,
            "user": user,
            "json_schema": json_schema,
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.cfg.api_key:
            req.add_header("Authorization", f"Bearer {self.cfg.api_key}")

        try:
            with urllib.request.urlopen(req, timeout=self.cfg.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["json"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"LLM HTTPError: {e.code} {e.reason}") from e
        except Exception as e:
            raise RuntimeError(f"LLM error: {e}") from e
