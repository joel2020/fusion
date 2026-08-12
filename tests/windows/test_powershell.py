import json
from subprocess import CompletedProcess
from unittest.mock import Mock

import pytest

from fusion_calling.windows import powershell


def test_rejects_unsupported_powershell_request() -> None:
    with pytest.raises(ValueError, match="unsupported PowerShell request"):
        powershell.PowerShellRunner().powershell_json("Get arbitrary script")


def test_runs_only_the_fixed_inventory_script(monkeypatch: pytest.MonkeyPatch) -> None:
    run = Mock(return_value=CompletedProcess([], 0, '{"computer_name":"Joel"}', ""))
    monkeypatch.setattr(powershell.subprocess, "run", run)

    powershell.PowerShellRunner().powershell_json("Get Fusion workstation inventory")

    run.assert_called_once_with(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            powershell.INVENTORY_SCRIPT,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_nonzero_powershell_exit_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    run = Mock(return_value=CompletedProcess([], 1, "", "access denied"))
    monkeypatch.setattr(powershell.subprocess, "run", run)

    with pytest.raises(RuntimeError, match="PowerShell inventory failed: access denied"):
        powershell.PowerShellRunner().powershell_json(
            "Get Fusion workstation inventory"
        )


def test_empty_powershell_output_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    run = Mock(return_value=CompletedProcess([], 0, "  \n", ""))
    monkeypatch.setattr(powershell.subprocess, "run", run)

    with pytest.raises(RuntimeError, match="PowerShell inventory returned no data"):
        powershell.PowerShellRunner().powershell_json(
            "Get Fusion workstation inventory"
        )


def test_invalid_powershell_json_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    run = Mock(return_value=CompletedProcess([], 0, "not-json", ""))
    monkeypatch.setattr(powershell.subprocess, "run", run)

    with pytest.raises(RuntimeError, match="PowerShell inventory returned invalid JSON"):
        powershell.PowerShellRunner().powershell_json(
            "Get Fusion workstation inventory"
        )


def test_valid_powershell_json_maps_to_dictionary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"computer_name": "Joel", "windows_build": "26200"}
    run = Mock(return_value=CompletedProcess([], 0, json.dumps(payload), ""))
    monkeypatch.setattr(powershell.subprocess, "run", run)

    result = powershell.PowerShellRunner().powershell_json(
        "Get Fusion workstation inventory"
    )

    assert result == payload
