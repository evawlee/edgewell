import io
import time
from typing import Iterable, List


class AuditLogEmitter:
    def __init__(self, sink=None):
        self._sink = sink if sink is not None else io.StringIO()

    def record_request(self, method: str, path: str, request_user: str, request_source: str, status: int) -> None:
        ts = int(time.time())
        line = f"{ts}\tREQ\t{method}\t{path}\tuser={request_user}\tsrc={request_source}\tstatus={status}\n"
        self._sink.write(line)

    def record_action(self, actor: str, action: str, target: str, outcome: str, detail: str = "") -> None:
        ts = int(time.time())
        line = f"{ts}\tACT\t{actor}\t{action}\t{target}\t{outcome}\t{detail}\n"
        self._sink.write(line)

    def record_upload(self, uploader: str, upload_id: str, filename: str, size_bytes: int, sha256: str) -> None:
        ts = int(time.time())
        line = f"{ts}\tUPL\t{uploader}\t{upload_id}\t{filename}\t{size_bytes}\t{sha256}\n"
        self._sink.write(line)

    def export(self) -> str:
        if hasattr(self._sink, "getvalue"):
            return self._sink.getvalue()
        return ""

    def lines(self) -> List[str]:
        text = self.export()
        return [l for l in text.split("\n") if l]

    def reset(self) -> None:
        if hasattr(self._sink, "truncate"):
            self._sink.seek(0)
            self._sink.truncate()


def parse_lines(text: str) -> List[Iterable[str]]:
    out = []
    for raw in text.split("\n"):
        if not raw:
            continue
        out.append(raw.split("\t"))
    return out
