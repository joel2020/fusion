import json
import sys
from types import SimpleNamespace

import pytest
from typer.main import get_command
from typer.testing import CliRunner

from fusion_calling import cli
from fusion_calling.models import DeviceInfo, PreflightReport
from fusion_calling.windows.audio import AudioEndpoint
from fusion_calling.windows.spoke import SpokeWindow


app = cli.app


runner = CliRunner()


def test_help_exposes_only_read_only_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "preflight" in result.stdout
    assert "audio-list" in result.stdout
    assert "spoke-inspect" in result.stdout
    assert "dial" not in result.stdout.lower()


def test_cli_registers_exactly_the_read_only_commands() -> None:
    command = get_command(app)

    assert set(command.commands) == {"preflight", "audio-list", "spoke-inspect"}


def test_preflight_prints_complete_report(monkeypatch: pytest.MonkeyPatch) -> None:
    report = PreflightReport(
        computer_name="Joel",
        windows_build="26200",
        spoke_version="10.18.0",
        chrome_version="140.0.0.0",
        audio_devices=(DeviceInfo(name="Realtek Audio", kind="sound", status="OK"),),
    )
    monkeypatch.setattr(cli, "collect_preflight", lambda runner: report)

    result = runner.invoke(app, ["preflight"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == report.model_dump(mode="json")


def test_preflight_fails_closed_when_required_component_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = PreflightReport(
        computer_name="Joel",
        windows_build="26200",
        spoke_version=None,
        chrome_version="140.0.0.0",
        audio_devices=(DeviceInfo(name="Realtek Audio", kind="sound", status="OK"),),
    )
    monkeypatch.setattr(cli, "collect_preflight", lambda runner: report)

    result = runner.invoke(app, ["preflight"])

    assert result.exit_code == 1
    assert result.stdout == ""


def test_audio_list_prints_endpoint_inventory(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = AudioEndpoint(
        index=2,
        name="Realtek Audio",
        inputs=2,
        outputs=2,
        default_sample_rate=48000,
    )
    monkeypatch.setattr(cli, "list_audio_endpoints", lambda query_devices: (endpoint,))

    result = runner.invoke(app, ["audio-list"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == [endpoint.model_dump()]


def test_spoke_inspect_prints_window_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    window = SpokeWindow(
        title="Spoke Phone",
        process_id=412,
        visible=True,
        enabled=True,
    )
    desktop = object()
    monkeypatch.setitem(
        sys.modules,
        "pywinauto",
        SimpleNamespace(Desktop=lambda *, backend: desktop),
    )
    monkeypatch.setattr(cli, "inspect_spoke", lambda actual, title: window)

    result = runner.invoke(app, ["spoke-inspect"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == window.model_dump()
