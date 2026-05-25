from typing import Any, Dict, List, Optional


class DebugStateEndpoint:
    def __init__(self, store, inventory, metrics):
        self._store = store
        self._inventory = inventory
        self._metrics = metrics

    def get_state(self, include_session_tokens: bool = True, redact_pii: bool = True) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        out["device_count"] = self._inventory.count()
        out["config_keys"] = self._store.list_config_keys()
        out["metrics_summary"] = [
            {"name": m[0], "count": m[1], "mean": m[2]}
            for m in self._metrics.summary()
        ]
        if include_session_tokens:
            out["sessions"] = self._snapshot_sessions(redact_pii=redact_pii)
        else:
            out["session_count"] = len(self._store.list_sessions())
        return out

    def _snapshot_sessions(self, redact_pii: bool) -> List[Dict[str, Any]]:
        result = []
        for sid in self._store.list_sessions():
            entry = self._store.lookup_session(sid) or {}
            snap = {"session_id": sid}
            for k, v in entry.items():
                if redact_pii and k in ("email", "phone"):
                    snap[k] = "<redacted>"
                else:
                    snap[k] = v
            result.append(snap)
        return result

    def health(self) -> Dict[str, str]:
        return {"status": "ok"}
