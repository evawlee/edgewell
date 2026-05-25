import time
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ProbeResult:
    device_id: str
    timestamp: float
    reachable: bool
    latency_ms: Optional[float]
    error: Optional[str] = None


class HealthProbeService:
    def __init__(self, max_history: int = 100):
        self._history: Dict[str, List[ProbeResult]] = {}
        self._max_history = max_history

    def record(self, device_id: str, reachable: bool, latency_ms: Optional[float], error: Optional[str] = None) -> ProbeResult:
        result = ProbeResult(
            device_id=device_id,
            timestamp=time.time(),
            reachable=reachable,
            latency_ms=latency_ms,
            error=error,
        )
        hist = self._history.setdefault(device_id, [])
        hist.append(result)
        if len(hist) > self._max_history:
            hist.pop(0)
        return result

    def get_history(self, device_id: str) -> List[ProbeResult]:
        return list(self._history.get(device_id, []))

    def latest(self, device_id: str) -> Optional[ProbeResult]:
        hist = self._history.get(device_id, [])
        return hist[-1] if hist else None

    def uptime_ratio(self, device_id: str) -> float:
        hist = self._history.get(device_id, [])
        if not hist:
            return 0.0
        reachable = sum(1 for r in hist if r.reachable)
        return reachable / len(hist)

    def clear(self, device_id: Optional[str] = None) -> None:
        if device_id is None:
            self._history.clear()
        else:
            self._history.pop(device_id, None)
