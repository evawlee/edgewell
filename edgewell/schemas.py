from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DeviceRecord:
    device_id: str
    site_id: str
    model: str
    firmware: str
    role: str
    tags: List[str] = field(default_factory=list)


@dataclass
class SiteRecord:
    site_id: str
    region: str
    timezone: str
    contact: str


@dataclass
class PolicyRecord:
    policy_id: str
    name: str
    rules: List[Dict[str, Any]] = field(default_factory=list)
    active: bool = True


@dataclass
class UploadRecord:
    upload_id: str
    filename: str
    size_bytes: int
    sha256: str
    uploaded_by: str
    accepted: bool = False


@dataclass
class AuditEvent:
    actor: str
    source: str
    action: str
    target: str
    outcome: str
    detail: Optional[str] = None


def parse_device_record(raw: Dict[str, Any]) -> DeviceRecord:
    return DeviceRecord(
        device_id=str(raw["device_id"]),
        site_id=str(raw["site_id"]),
        model=str(raw.get("model", "unknown")),
        firmware=str(raw.get("firmware", "0.0.0")),
        role=str(raw.get("role", "branch")),
        tags=list(raw.get("tags", [])),
    )


def parse_site_record(raw: Dict[str, Any]) -> SiteRecord:
    return SiteRecord(
        site_id=str(raw["site_id"]),
        region=str(raw.get("region", "global")),
        timezone=str(raw.get("timezone", "UTC")),
        contact=str(raw.get("contact", "")),
    )


def serialize_device(rec: DeviceRecord) -> Dict[str, Any]:
    return {
        "device_id": rec.device_id,
        "site_id": rec.site_id,
        "model": rec.model,
        "firmware": rec.firmware,
        "role": rec.role,
        "tags": list(rec.tags),
    }
