from __future__ import annotations
from typing import Any, Dict

class AuditRepository:
    """
    MVP: imprime/loga. Produção: grava em DB.
    """
    def save(self, record: Dict[str, Any]) -> None:
        # Troque por insert no DB.
        # Não salve ementa inteira aqui. Salve hashes e evidências mínimas.
        pass
