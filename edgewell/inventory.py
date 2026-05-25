from typing import Dict, Iterable, List, Optional

from .schemas import DeviceRecord, parse_device_record, serialize_device


class DeviceInventory:
    def __init__(self):
        self._devices: Dict[str, DeviceRecord] = {}
        self._by_site: Dict[str, List[str]] = {}

    def add(self, raw: dict) -> DeviceRecord:
        rec = parse_device_record(raw)
        self._devices[rec.device_id] = rec
        self._by_site.setdefault(rec.site_id, []).append(rec.device_id)
        return rec

    def get(self, device_id: str) -> Optional[DeviceRecord]:
        return self._devices.get(device_id)

    def list_for_site(self, site_id: str) -> List[DeviceRecord]:
        ids = self._by_site.get(site_id, [])
        return [self._devices[i] for i in ids if i in self._devices]

    def remove(self, device_id: str) -> bool:
        rec = self._devices.pop(device_id, None)
        if rec is None:
            return False
        site = self._by_site.get(rec.site_id, [])
        if device_id in site:
            site.remove(device_id)
        return True

    def export_all(self) -> List[dict]:
        return [serialize_device(r) for r in self._devices.values()]

    def count(self) -> int:
        return len(self._devices)


def filter_by_role(devices: Iterable[DeviceRecord], role: str) -> List[DeviceRecord]:
    return [d for d in devices if d.role == role]


def filter_by_firmware(devices: Iterable[DeviceRecord], firmware: str) -> List[DeviceRecord]:
    return [d for d in devices if d.firmware == firmware]
