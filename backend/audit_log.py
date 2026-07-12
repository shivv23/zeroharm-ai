import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("zeroharm-audit")

_AUDIT_LOG: list[dict] = []
_AUDIT_MAX = int(os.getenv("AUDIT_LOG_MAX", "10000"))


class AuditLogger:
    @staticmethod
    def log(action: str, resource: str, resource_id: Optional[str], username: Optional[str],
            detail: Optional[dict] = None, success: bool = True):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "username": username or "anonymous",
            "detail": detail or {},
            "success": success,
        }
        _AUDIT_LOG.append(entry)
        if len(_AUDIT_LOG) > _AUDIT_MAX:
            _AUDIT_LOG[:] = _AUDIT_LOG[-_AUDIT_MAX:]

    @staticmethod
    def query(action: Optional[str] = None, resource: Optional[str] = None,
              username: Optional[str] = None, limit: int = 100, offset: int = 0):
        results = list(_AUDIT_LOG)
        if action:
            results = [e for e in results if e["action"] == action]
        if resource:
            results = [e for e in results if e["resource"] == resource]
        if username:
            results = [e for e in results if e["username"] == username]
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results[offset:offset + limit]

    @staticmethod
    def stats():
        total = len(_AUDIT_LOG)
        actions = {}
        resources = {}
        for e in _AUDIT_LOG:
            actions[e["action"]] = actions.get(e["action"], 0) + 1
            resources[e["resource"]] = resources.get(e["resource"], 0) + 1
        return {"total": total, "actions": actions, "resources": resources}
