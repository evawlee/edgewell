import re
from typing import Any, Dict


_VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\}")


class TemplateEngine:
    def __init__(self):
        self._templates: Dict[str, str] = {}

    def register(self, name: str, body: str) -> None:
        self._templates[name] = body

    def get(self, name: str) -> str:
        if name not in self._templates:
            raise KeyError(name)
        return self._templates[name]

    def render(self, name: str, context: Dict[str, Any]) -> str:
        body = self.get(name)
        return self._substitute(body, context)

    def render_string(self, body: str, context: Dict[str, Any]) -> str:
        return self._substitute(body, context)

    def _substitute(self, body: str, context: Dict[str, Any]) -> str:
        def repl(match):
            key = match.group(1)
            return str(_resolve(context, key))
        return _VAR_PATTERN.sub(repl, body)

    def list_templates(self):
        return list(self._templates.keys())


def _resolve(ctx: Dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    cur: Any = ctx
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return ""
    return cur
