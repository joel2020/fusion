from typing import Protocol

from fusion_calling.models import PreflightReport


class CommandRunner(Protocol):
    def powershell_json(self, script: str) -> dict: ...


def collect_preflight(runner: CommandRunner) -> PreflightReport:
    return PreflightReport.model_validate(
        runner.powershell_json("Get Fusion workstation inventory")
    )
