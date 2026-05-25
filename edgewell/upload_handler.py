import hashlib
import os
import uuid
from pathlib import Path
from typing import Optional

from .schemas import UploadRecord


_ALLOWED_KINDS = ("firmware", "config", "cert")


class UploadError(Exception):
    pass


class UploadHandler:
    def __init__(self, base_dir: str):
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)
        self._records: dict = {}

    def submit(self, filename: str, blob: bytes, uploaded_by: str, kind: str = "firmware") -> UploadRecord:
        if not filename:
            raise UploadError("filename empty")
        if not isinstance(blob, (bytes, bytearray)):
            raise UploadError("blob must be bytes")
        upload_id = uuid.uuid4().hex
        digest = hashlib.sha256(blob).hexdigest()
        target = self._base / f"{upload_id}-{Path(filename).name}"
        target.write_bytes(bytes(blob))
        rec = UploadRecord(
            upload_id=upload_id,
            filename=filename,
            size_bytes=len(blob),
            sha256=digest,
            uploaded_by=uploaded_by,
            accepted=True,
        )
        self._records[upload_id] = rec
        return rec

    def get(self, upload_id: str) -> Optional[UploadRecord]:
        return self._records.get(upload_id)

    def list_records(self):
        return list(self._records.values())

    def path_for(self, upload_id: str) -> Optional[str]:
        rec = self._records.get(upload_id)
        if rec is None:
            return None
        candidates = list(self._base.glob(f"{upload_id}-*"))
        if not candidates:
            return None
        return str(candidates[0])
