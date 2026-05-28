import io
import subprocess

import pytest

from edgewell.api import ManagementApp
from edgewell.audit_log import AuditLogEmitter, parse_lines
from edgewell.cli_runner import CliResult, DiagRunner
from edgewell.config_store import ConfigStore
from edgewell.debug_endpoint import DebugStateEndpoint
from edgewell.health_probe import HealthProbeService
from edgewell.inventory import DeviceInventory, filter_by_role
from edgewell.metrics import MetricsCollector
from edgewell.policy_loader import PolicyLoader
from edgewell.schemas import (
    DeviceRecord,
    parse_device_record,
    serialize_device,
)
from edgewell.template_engine import TemplateEngine
from edgewell.upload_handler import UploadError, UploadHandler


def test_device_record_round_trip():
    raw = {"device_id": "d1", "site_id": "s1", "model": "rt100", "firmware": "1.2.3", "role": "branch"}
    rec = parse_device_record(raw)
    assert rec.device_id == "d1"
    assert rec.firmware == "1.2.3"
    assert serialize_device(rec)["device_id"] == "d1"


def test_inventory_add_and_lookup():
    inv = DeviceInventory()
    inv.add({"device_id": "d1", "site_id": "s1", "model": "rt100"})
    inv.add({"device_id": "d2", "site_id": "s1", "model": "rt100"})
    inv.add({"device_id": "d3", "site_id": "s2", "model": "rt200"})
    assert inv.count() == 3
    assert inv.get("d1").device_id == "d1"
    site1 = inv.list_for_site("s1")
    assert len(site1) == 2


def test_inventory_remove():
    inv = DeviceInventory()
    inv.add({"device_id": "d1", "site_id": "s1"})
    assert inv.remove("d1") is True
    assert inv.get("d1") is None
    assert inv.remove("d1") is False


def test_inventory_filter_by_role():
    inv = DeviceInventory()
    inv.add({"device_id": "d1", "site_id": "s1", "role": "branch"})
    inv.add({"device_id": "d2", "site_id": "s1", "role": "hub"})
    inv.add({"device_id": "d3", "site_id": "s1", "role": "branch"})
    all_records = [inv.get(d) for d in ("d1", "d2", "d3")]
    branches = filter_by_role(all_records, "branch")
    assert len(branches) == 2


def test_health_probe_record_and_uptime():
    svc = HealthProbeService()
    svc.record("d1", True, 12.5)
    svc.record("d1", True, 11.0)
    svc.record("d1", False, None, error="timeout")
    assert len(svc.get_history("d1")) == 3
    assert svc.latest("d1").reachable is False
    assert svc.uptime_ratio("d1") == pytest.approx(2 / 3)


def test_health_probe_clear():
    svc = HealthProbeService()
    svc.record("d1", True, 5.0)
    svc.clear("d1")
    assert svc.get_history("d1") == []


def test_metrics_record_and_summary():
    m = MetricsCollector()
    m.record("link.latency_ms", 5.0)
    m.record("link.latency_ms", 7.0)
    m.record("link.latency_ms", 9.0)
    summary = dict((s[0], s) for s in m.summary())
    name, count, mean, mn, mx = summary["link.latency_ms"]
    assert count == 3
    assert mean == pytest.approx(7.0)
    assert mn == 5.0
    assert mx == 9.0


def test_metrics_reset_all():
    m = MetricsCollector()
    m.record("a", 1.0)
    m.record("b", 2.0)
    m.reset_all()
    summary = dict((s[0], s) for s in m.summary())
    assert summary["a"][1] == 0


def test_policy_loader_load_and_list():
    pl = PolicyLoader()
    pl.load_from_dict({"policy_id": "p1", "name": "default", "rules": [{"k": "v"}]})
    pl.load_from_dict({"policy_id": "p2", "name": "branch", "rules": []})
    assert pl.count() == 2
    actives = pl.list_active()
    assert {p.policy_id for p in actives} == {"p1", "p2"}


def test_policy_loader_disable():
    pl = PolicyLoader()
    pl.load_from_dict({"policy_id": "p1"})
    assert pl.disable("p1") is True
    assert len(pl.list_active()) == 0
    assert pl.enable("p1") is True
    assert len(pl.list_active()) == 1


def test_template_engine_render():
    te = TemplateEngine()
    te.register("hello", "site={{ site.id }}, role={{ role }}")
    out = te.render("hello", {"site": {"id": "s1"}, "role": "branch"})
    assert out == "site=s1, role=branch"


def test_template_engine_unknown_var_empty():
    te = TemplateEngine()
    out = te.render_string("a={{missing}}", {})
    assert out == "a="


def test_config_store_put_get():
    store = ConfigStore()
    store.put_config("k1", {"a": 1})
    store.put_config("k2", {"b": 2})
    assert store.get_config("k1") == {"a": 1}
    assert set(store.list_config_keys()) >= {"k1", "k2"}
    store.clear()


def test_config_store_session_put_get():
    store = ConfigStore()
    store.open_session("sid1", {"user": "alice"})
    assert store.lookup_session("sid1") == {"user": "alice"}
    assert store.close_session("sid1") is True
    assert store.lookup_session("sid1") is None
    store.clear()


def test_upload_handler_accepts_firmware(tmp_path):
    u = UploadHandler(str(tmp_path))
    rec = u.submit("v1.bin", b"\x00\x01\x02", "alice", kind="firmware")
    assert rec.accepted is True
    assert rec.size_bytes == 3
    assert rec.uploaded_by == "alice"


def test_upload_handler_accepts_config(tmp_path):
    u = UploadHandler(str(tmp_path))
    rec = u.submit("running.cfg", b"abcdef", "noc", kind="config")
    assert rec.accepted is True


def test_upload_handler_rejects_empty_filename(tmp_path):
    u = UploadHandler(str(tmp_path))
    with pytest.raises(UploadError):
        u.submit("", b"x", "alice")


def test_diag_runner_returns_cliresult_on_unknown_target(monkeypatch):
    captured = []

    def fake_run(*args, **kwargs):
        captured.append((args, kwargs))

        class C:
            returncode = 0
            stdout = "ok"
            stderr = ""
        return C()

    monkeypatch.setattr(subprocess, "run", fake_run)
    r = DiagRunner()
    res = r.run_ping("10.0.0.1")
    assert isinstance(res, CliResult)
    assert res.returncode == 0


def test_diag_runner_traceroute_invokes_subprocess(monkeypatch):
    captured = []

    def fake_run(*args, **kwargs):
        captured.append((args, kwargs))

        class C:
            returncode = 0
            stdout = ""
            stderr = ""
        return C()

    monkeypatch.setattr(subprocess, "run", fake_run)
    r = DiagRunner()
    r.run_traceroute("10.0.0.1")
    assert len(captured) == 1


def test_diag_runner_snmpget_invokes_subprocess(monkeypatch):
    captured = []

    def fake_run(*args, **kwargs):
        captured.append((args, kwargs))

        class C:
            returncode = 0
            stdout = ""
            stderr = ""
        return C()

    monkeypatch.setattr(subprocess, "run", fake_run)
    r = DiagRunner()
    r.run_snmpget("10.0.0.1", "1.3.6.1.2.1")
    assert len(captured) == 1


def test_diag_runner_snmpwalk_invokes_subprocess(monkeypatch):
    captured = []

    def fake_run(*args, **kwargs):
        captured.append((args, kwargs))

        class C:
            returncode = 0
            stdout = ""
            stderr = ""
        return C()

    monkeypatch.setattr(subprocess, "run", fake_run)
    r = DiagRunner()
    r.run_snmpwalk("10.0.0.1", "1.3.6.1.2.1")
    assert len(captured) == 1


def test_audit_log_records_request():
    a = AuditLogEmitter()
    a.record_request("GET", "/devices", "alice", "10.0.0.5", 200)
    text = a.export()
    assert "REQ" in text
    assert "alice" in text
    assert "10.0.0.5" in text


def test_audit_log_records_action():
    a = AuditLogEmitter()
    a.record_action("alice", "rotate_key", "device:d1", "ok", "manual")
    parsed = parse_lines(a.export())
    assert len(parsed) == 1
    assert parsed[0][1] == "ACT"


def test_audit_log_records_upload():
    a = AuditLogEmitter()
    a.record_upload("noc", "uid1", "fw.bin", 1024, "deadbeef")
    text = a.export()
    assert "UPL" in text
    assert "uid1" in text


def test_audit_log_reset():
    a = AuditLogEmitter()
    a.record_action("alice", "x", "y", "ok")
    a.reset()
    assert a.export() == ""


def test_debug_endpoint_health():
    store = ConfigStore()
    inv = DeviceInventory()
    m = MetricsCollector()
    d = DebugStateEndpoint(store, inv, m)
    assert d.health() == {"status": "ok"}
    store.clear()


def test_management_app_handle_request(tmp_path):
    app = ManagementApp(str(tmp_path / "uploads"))
    out = app.handle_request("GET", "/api/devices", "alice", "10.0.0.1")
    assert out == {"ok": True, "path": "/api/devices"}
    app.store.clear()


def test_management_app_upload_round_trip(tmp_path):
    app = ManagementApp(str(tmp_path / "uploads"))
    r = app.handle_upload("config.json", b"{}", "noc")
    assert "upload_id" in r
    assert r["accepted"] is True
    app.store.clear()
