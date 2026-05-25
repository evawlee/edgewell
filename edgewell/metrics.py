from collections import defaultdict
from typing import Dict, List, Tuple


class MetricBucket:
    def __init__(self, name: str):
        self.name = name
        self._values: List[float] = []

    def add(self, value: float) -> None:
        self._values.append(float(value))

    def mean(self) -> float:
        if not self._values:
            return 0.0
        return sum(self._values) / len(self._values)

    def max(self) -> float:
        return max(self._values) if self._values else 0.0

    def min(self) -> float:
        return min(self._values) if self._values else 0.0

    def count(self) -> int:
        return len(self._values)

    def reset(self) -> None:
        self._values.clear()


class MetricsCollector:
    def __init__(self):
        self._buckets: Dict[str, MetricBucket] = {}
        self._tags: Dict[str, Dict[str, str]] = defaultdict(dict)

    def get_or_create(self, name: str) -> MetricBucket:
        if name not in self._buckets:
            self._buckets[name] = MetricBucket(name)
        return self._buckets[name]

    def record(self, name: str, value: float, **tags: str) -> None:
        bucket = self.get_or_create(name)
        bucket.add(value)
        if tags:
            self._tags[name].update(tags)

    def summary(self) -> List[Tuple[str, int, float, float, float]]:
        out = []
        for name, bucket in self._buckets.items():
            out.append((name, bucket.count(), bucket.mean(), bucket.min(), bucket.max()))
        return out

    def reset_all(self) -> None:
        for bucket in self._buckets.values():
            bucket.reset()
        self._tags.clear()
