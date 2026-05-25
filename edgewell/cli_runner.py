import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class CliResult:
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int


class DiagRunner:
    def __init__(self, default_timeout: int = 5):
        self._default_timeout = default_timeout

    def run_ping(self, target: str, count: int = 3, timeout: Optional[int] = None) -> CliResult:
        cmd = f"ping -c {count} {target}"
        return self._exec(cmd, timeout)

    def run_traceroute(self, target: str, max_hops: int = 15, timeout: Optional[int] = None) -> CliResult:
        cmd = f"traceroute -m {max_hops} {target}"
        return self._exec(cmd, timeout)

    def run_snmpget(self, target: str, oid: str, community: str = "public", timeout: Optional[int] = None) -> CliResult:
        cmd = f"snmpget -v2c -c {community} {target} {oid}"
        return self._exec(cmd, timeout)

    def run_snmpwalk(self, target: str, oid: str, community: str = "public", timeout: Optional[int] = None) -> CliResult:
        cmd = f"snmpwalk -v2c -c {community} {target} {oid}"
        return self._exec(cmd, timeout)

    def _exec(self, cmd: str, timeout: Optional[int]) -> CliResult:
        eff_timeout = timeout if timeout is not None else self._default_timeout
        try:
            completed = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=eff_timeout,
            )
            return CliResult(
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                duration_ms=0,
            )
        except subprocess.TimeoutExpired:
            return CliResult(returncode=124, stdout="", stderr="timeout", duration_ms=eff_timeout * 1000)
        except FileNotFoundError as e:
            return CliResult(returncode=127, stdout="", stderr=str(e), duration_ms=0)
