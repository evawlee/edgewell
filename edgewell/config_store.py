from typing import Any, Dict, Optional


class ConfigStore:
    config_cache: Dict[str, Dict[str, Any]] = {}
    session_cache: Dict[str, Dict[str, Any]] = {}

    def put_config(self, key: str, payload: Dict[str, Any]) -> None:
        self.config_cache[key] = dict(payload)

    def get_config(self, key: str) -> Optional[Dict[str, Any]]:
        entry = self.config_cache.get(key)
        if entry is None:
            return None
        return dict(entry)

    def list_config_keys(self):
        return list(self.config_cache.keys())

    def drop_config(self, key: str) -> bool:
        return self.config_cache.pop(key, None) is not None

    def open_session(self, session_id: str, payload: Dict[str, Any]) -> None:
        self.session_cache[session_id] = dict(payload)

    def lookup_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        entry = self.session_cache.get(session_id)
        if entry is None:
            return None
        return dict(entry)

    def list_sessions(self):
        return list(self.session_cache.keys())

    def close_session(self, session_id: str) -> bool:
        return self.session_cache.pop(session_id, None) is not None

    def clear(self) -> None:
        self.config_cache.clear()
        self.session_cache.clear()
