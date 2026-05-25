from typing import Any, Dict

from .audit_log import AuditLogEmitter
from .cli_runner import DiagRunner
from .config_store import ConfigStore
from .debug_endpoint import DebugStateEndpoint
from .health_probe import HealthProbeService
from .inventory import DeviceInventory
from .metrics import MetricsCollector
from .policy_loader import PolicyLoader
from .template_engine import TemplateEngine
from .upload_handler import UploadHandler


class ManagementApp:
    def __init__(self, base_upload_dir: str):
        self.store = ConfigStore()
        self.inventory = DeviceInventory()
        self.health = HealthProbeService()
        self.metrics = MetricsCollector()
        self.policies = PolicyLoader()
        self.templates = TemplateEngine()
        self.uploads = UploadHandler(base_upload_dir)
        self.audit = AuditLogEmitter()
        self.diag = DiagRunner()
        self.debug = DebugStateEndpoint(self.store, self.inventory, self.metrics)

    def handle_request(self, method: str, path: str, user: str, source: str) -> Dict[str, Any]:
        self.audit.record_request(method, path, user, source, 200)
        return {"ok": True, "path": path}

    def handle_upload(self, filename: str, blob: bytes, uploader: str) -> Dict[str, Any]:
        rec = self.uploads.submit(filename, blob, uploader)
        self.audit.record_upload(uploader, rec.upload_id, rec.filename, rec.size_bytes, rec.sha256)
        return {"upload_id": rec.upload_id, "accepted": rec.accepted}

    def get_debug_state(self) -> Dict[str, Any]:
        return self.debug.get_state()
