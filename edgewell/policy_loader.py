import json
from typing import Any, Dict, List, Optional

from .schemas import PolicyRecord


class PolicyLoader:
    def __init__(self):
        self._policies: Dict[str, PolicyRecord] = {}
        self._load_order: List[str] = []

    def load_from_dict(self, raw: Dict[str, Any]) -> PolicyRecord:
        policy = PolicyRecord(
            policy_id=str(raw["policy_id"]),
            name=str(raw.get("name", raw["policy_id"])),
            rules=list(raw.get("rules", [])),
            active=bool(raw.get("active", True)),
        )
        if policy.policy_id not in self._policies:
            self._load_order.append(policy.policy_id)
        self._policies[policy.policy_id] = policy
        return policy

    def load_from_json(self, text: str) -> PolicyRecord:
        return self.load_from_dict(json.loads(text))

    def get(self, policy_id: str) -> Optional[PolicyRecord]:
        return self._policies.get(policy_id)

    def list_active(self) -> List[PolicyRecord]:
        return [self._policies[pid] for pid in self._load_order if self._policies[pid].active]

    def disable(self, policy_id: str) -> bool:
        p = self._policies.get(policy_id)
        if p is None:
            return False
        p.active = False
        return True

    def enable(self, policy_id: str) -> bool:
        p = self._policies.get(policy_id)
        if p is None:
            return False
        p.active = True
        return True

    def count(self) -> int:
        return len(self._policies)
