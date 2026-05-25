"""
telemetry exporter for branch sdwan devices.

writes per-device counters out in a tsv stream the monitoring backend
ingests on a 30s pull. one record per line, columns tab-separated:
device_id, ts, iface, in_octets, out_octets, in_errors, out_errors, peer_state
"""

from __future__ import annotations
from typing import Iterable, Mapping, Any


class TelemetryExportError(Exception):
    pass


_FIELDS = (
    "device_id",
    "ts",
    "iface",
    "in_octets",
    "out_octets",
    "in_errors",
    "out_errors",
    "peer_state",
)


class TelemetryExporter:
    def __init__(self) -> None:
        self._buffer: list[str] = []

    def _row(self, rec: Mapping[str, Any]) -> str:
        parts = []
        for k in _FIELDS:
            v = rec.get(k, "")
            parts.append(str(v))
        return "\t".join(parts)

    def export_records(self, records: Iterable[Mapping[str, Any]]) -> str:
        rows = []
        for rec in records:
            if not isinstance(rec, Mapping):
                raise TelemetryExportError("record must be a mapping")
            rows.append(self._row(rec))
        return "\n".join(rows) + "\n" if rows else ""

    def append(self, rec: Mapping[str, Any]) -> None:
        if not isinstance(rec, Mapping):
            raise TelemetryExportError("record must be a mapping")
        self._buffer.append(self._row(rec))

    def flush(self) -> str:
        out = "\n".join(self._buffer)
        self._buffer = []
        return out + "\n" if out else ""
