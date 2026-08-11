# Lenovo Calling Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the Windows foundation for Joel's dedicated calling workstation without placing prospect calls or changing Zoho data.

**Architecture:** A small Python application runs locally on the Lenovo and exposes explicit preflight, dry-run, and test-only commands. Windows adapters discover audio devices and SpokePhone without changing them, while a state machine and test-number allowlist prevent accidental dialing. Later phases consume these interfaces for ElevenLabs audio, SpokePhone control, and Zoho workflows.

**Tech Stack:** Python 3.12, Pydantic 2, Typer, pytest, Windows PowerShell, pywinauto, sounddevice

## Global Constraints

- Run on Lenovo Yoga 7 model 83JT with Windows 11 Home build 26200.
- Spoke Phone 10.18.0 remains the only telephone dialer.
- No prospect calls or Zoho writes are allowed in this phase.
- Later dialing phases must reject any cold-call lead whose owner is not exactly `Fusion House Account`.
- Unanswered and no-meeting outcomes retain owner `Fusion House Account`; callback and EOI outcomes change owner to `Joel Carias`.
- Only explicitly configured internal test numbers may pass the dialing safety gate.
- Keep one-call-at-a-time state and fail closed on missing configuration, unexpected UI, or audio errors.
- Never read or export browser cookies, passwords, OAuth tokens, or ElevenLabs secrets.
- Store secrets only in the current Windows user's environment or Windows Credential Manager; never commit them.
- The existing Tailscale SSH firewall restriction to `100.107.28.56` remains unchanged.

## Roadmap Boundaries

This plan implements Phase 1 only. Separate plans are required for:

1. ElevenLabs conversational audio and internal test calls.
2. Zoho lead selection, double dialing, voicemail, and notes.
3. Outlook availability, Zoho Bookings, and CRM Blueprint transitions.
4. Callback tasks, reminder texts, supervised pilot, and unattended operations.

The owner-transition behavior belongs to the later Zoho lead-handling plan. Phase 1 preserves the exact owner names as global constraints but performs no Zoho reads or writes.

## File Map

- `pyproject.toml`: Python version, runtime dependencies, test dependencies, and console command.
- `src/fusion_calling/__init__.py`: package version.
- `src/fusion_calling/config.py`: validated local configuration and safe defaults.
- `src/fusion_calling/models.py`: device, preflight, and workstation-state types.
- `src/fusion_calling/safety.py`: test-number allowlist and single-call interlock.
- `src/fusion_calling/windows/preflight.py`: read-only Windows, SpokePhone, Chrome, and audio discovery.
- `src/fusion_calling/windows/audio.py`: audio-device inventory and route validation.
- `src/fusion_calling/windows/spoke.py`: read-only SpokePhone window discovery.
- `src/fusion_calling/cli.py`: `preflight`, `audio-list`, and `spoke-inspect` commands.
- `tests/`: unit tests using fakes; tests never operate SpokePhone or Windows UI.
- `config/fusion-calling.example.toml`: non-secret example configuration with dialing disabled.

---

### Task 1: Package Skeleton and Safe Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `src/fusion_calling/__init__.py`
- Create: `src/fusion_calling/config.py`
- Create: `config/fusion-calling.example.toml`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces: `CallingConfig.load(path: Path) -> CallingConfig`
- Produces: `CallingConfig.dialing_enabled: bool`
- Produces: `CallingConfig.allowed_test_numbers: tuple[str, ...]`
- Produces: `CallingConfig.spoke_window_pattern: str`

- [ ] **Step 1: Write the failing configuration tests**

```python
from pathlib import Path

import pytest

from fusion_calling.config import CallingConfig


def test_defaults_disable_dialing(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[workstation]\nspoke_window_pattern = "Spoke Phone"\n')
    config = CallingConfig.load(path)
    assert config.dialing_enabled is False
    assert config.allowed_test_numbers == ()


def test_enabled_dialing_requires_test_number(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[workstation]\ndialing_enabled = true\nspoke_window_pattern = "Spoke Phone"\n')
    with pytest.raises(ValueError, match="allowed_test_numbers"):
        CallingConfig.load(path)
```

- [ ] **Step 2: Run the tests and verify the expected import failure**

Run: `py -m pytest tests/test_config.py -v`

Expected: FAIL because `fusion_calling.config` does not exist.

- [ ] **Step 3: Create the package and validated configuration**

```python
# src/fusion_calling/config.py
from pathlib import Path
import tomllib

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class CallingConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    dialing_enabled: bool = False
    allowed_test_numbers: tuple[str, ...] = ()
    spoke_window_pattern: str = "Spoke Phone"

    @field_validator("allowed_test_numbers")
    @classmethod
    def normalize_numbers(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = []
        for value in values:
            digits = "".join(character for character in value if character.isdigit())
            if len(digits) == 10:
                digits = "1" + digits
            if len(digits) != 11 or not digits.startswith("1"):
                raise ValueError("test numbers must be valid US numbers")
            normalized.append("+" + digits)
        return tuple(normalized)

    @model_validator(mode="after")
    def require_allowlist_when_enabled(self) -> "CallingConfig":
        if self.dialing_enabled and not self.allowed_test_numbers:
            raise ValueError("allowed_test_numbers is required when dialing is enabled")
        return self

    @classmethod
    def load(cls, path: Path) -> "CallingConfig":
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
        return cls.model_validate(payload.get("workstation", {}))
```

Create `src/fusion_calling/__init__.py` with `__version__ = "0.1.0"` and create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "fusion-calling"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "pydantic>=2.8,<3",
  "typer>=0.12,<1",
  "pywinauto>=0.6.9,<1",
  "sounddevice>=0.5,<1",
]

[project.optional-dependencies]
dev = ["pytest>=8,<9"]

[project.scripts]
fusion-calling = "fusion_calling.cli:app"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Create `config/fusion-calling.example.toml`:

```toml
[workstation]
dialing_enabled = false
allowed_test_numbers = []
spoke_window_pattern = "Spoke Phone"
```

- [ ] **Step 4: Run the configuration tests**

Run: `py -m pytest tests/test_config.py -v`

Expected: 2 tests PASS.

- [ ] **Step 5: Commit the configuration foundation**

```powershell
git add pyproject.toml src/fusion_calling/__init__.py src/fusion_calling/config.py config/fusion-calling.example.toml tests/test_config.py
git commit -m "feat: add safe calling configuration"
```

### Task 2: Workstation Preflight Inventory

**Files:**
- Create: `src/fusion_calling/models.py`
- Create: `src/fusion_calling/windows/__init__.py`
- Create: `src/fusion_calling/windows/preflight.py`
- Create: `tests/windows/test_preflight.py`

**Interfaces:**
- Produces: `DeviceInfo(name: str, kind: str, status: str)`
- Produces: `PreflightReport(computer_name: str, windows_build: str, spoke_version: str | None, chrome_version: str | None, audio_devices: tuple[DeviceInfo, ...], errors: tuple[str, ...])`
- Produces: `collect_preflight(runner: CommandRunner) -> PreflightReport`
- Consumes: no mutable Windows state; every command is read-only.

- [ ] **Step 1: Write a failing preflight test using a fake command runner**

```python
from fusion_calling.windows.preflight import collect_preflight


class FakeRunner:
    def powershell_json(self, script: str) -> dict:
        return {
            "computer_name": "Joel",
            "windows_build": "26200",
            "spoke_version": "10.18.0",
            "chrome_version": "151.0.7922.138",
            "audio_devices": [
                {"name": "Realtek High Definition Audio(SST)", "kind": "sound", "status": "OK"}
            ],
        }


def test_collect_preflight_maps_inventory() -> None:
    report = collect_preflight(FakeRunner())
    assert report.computer_name == "Joel"
    assert report.windows_build == "26200"
    assert report.spoke_version == "10.18.0"
    assert report.audio_devices[0].status == "OK"
    assert report.errors == ()
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `py -m pytest tests/windows/test_preflight.py -v`

Expected: FAIL because the models and preflight module do not exist.

- [ ] **Step 3: Implement immutable report models and the mapper**

```python
# src/fusion_calling/models.py
from pydantic import BaseModel, ConfigDict


class DeviceInfo(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    kind: str
    status: str


class PreflightReport(BaseModel):
    model_config = ConfigDict(frozen=True)
    computer_name: str
    windows_build: str
    spoke_version: str | None
    chrome_version: str | None
    audio_devices: tuple[DeviceInfo, ...]
    errors: tuple[str, ...] = ()
```

```python
# src/fusion_calling/windows/preflight.py
from typing import Protocol

from fusion_calling.models import PreflightReport


class CommandRunner(Protocol):
    def powershell_json(self, script: str) -> dict: ...


def collect_preflight(runner: CommandRunner) -> PreflightReport:
    return PreflightReport.model_validate(runner.powershell_json("Get Fusion workstation inventory"))
```

The production command runner added in Task 6 must implement the descriptive inventory request with `Get-ComputerInfo`, uninstall-registry reads, `Get-CimInstance Win32_SoundDevice`, and explicit Chrome executable version checks. It must not install, start, stop, or reconfigure applications.

- [ ] **Step 4: Run the preflight test**

Run: `py -m pytest tests/windows/test_preflight.py -v`

Expected: 1 test PASS.

- [ ] **Step 5: Commit the preflight model**

```powershell
git add src/fusion_calling/models.py src/fusion_calling/windows/__init__.py src/fusion_calling/windows/preflight.py tests/windows/test_preflight.py
git commit -m "feat: add read-only workstation preflight"
```

### Task 3: Dialing Safety Gate and Single-Call Interlock

**Files:**
- Create: `src/fusion_calling/safety.py`
- Create: `tests/test_safety.py`

**Interfaces:**
- Produces: `normalize_us_number(value: str) -> str`
- Produces: `DialSafetyGate.authorize(number: str) -> str`
- Produces: `CallInterlock.acquire(call_id: str) -> None`
- Produces: `CallInterlock.release(call_id: str) -> None`
- Consumes: `CallingConfig.dialing_enabled` and `CallingConfig.allowed_test_numbers`

- [ ] **Step 1: Write failing safety tests**

```python
import pytest

from fusion_calling.config import CallingConfig
from fusion_calling.safety import CallInterlock, DialSafetyGate


def test_gate_rejects_all_numbers_when_disabled() -> None:
    gate = DialSafetyGate(CallingConfig())
    with pytest.raises(PermissionError, match="disabled"):
        gate.authorize("813-555-0100")


def test_gate_accepts_only_allowlisted_number() -> None:
    config = CallingConfig(dialing_enabled=True, allowed_test_numbers=("813-555-0100",))
    gate = DialSafetyGate(config)
    assert gate.authorize("(813) 555-0100") == "+18135550100"
    with pytest.raises(PermissionError, match="allowlist"):
        gate.authorize("813-555-0101")


def test_interlock_rejects_second_active_call() -> None:
    interlock = CallInterlock()
    interlock.acquire("call-1")
    with pytest.raises(RuntimeError, match="already active"):
        interlock.acquire("call-2")
    interlock.release("call-1")
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `py -m pytest tests/test_safety.py -v`

Expected: FAIL because `fusion_calling.safety` does not exist.

- [ ] **Step 3: Implement the minimal fail-closed safety controls**

```python
# src/fusion_calling/safety.py
from dataclasses import dataclass

from fusion_calling.config import CallingConfig


def normalize_us_number(value: str) -> str:
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) == 10:
        digits = "1" + digits
    if len(digits) != 11 or not digits.startswith("1"):
        raise ValueError("number must be a valid US number")
    return "+" + digits


class DialSafetyGate:
    def __init__(self, config: CallingConfig) -> None:
        self._config = config

    def authorize(self, number: str) -> str:
        if not self._config.dialing_enabled:
            raise PermissionError("dialing is disabled")
        normalized = normalize_us_number(number)
        if normalized not in self._config.allowed_test_numbers:
            raise PermissionError("number is not on the internal test allowlist")
        return normalized


@dataclass
class CallInterlock:
    active_call_id: str | None = None

    def acquire(self, call_id: str) -> None:
        if self.active_call_id is not None:
            raise RuntimeError("a call is already active")
        self.active_call_id = call_id

    def release(self, call_id: str) -> None:
        if self.active_call_id != call_id:
            raise RuntimeError("call id does not own the interlock")
        self.active_call_id = None
```

- [ ] **Step 4: Run the safety tests**

Run: `py -m pytest tests/test_safety.py -v`

Expected: 3 tests PASS.

- [ ] **Step 5: Commit the safety gate**

```powershell
git add src/fusion_calling/safety.py tests/test_safety.py
git commit -m "feat: add fail-closed dialing interlock"
```

### Task 4: Audio Inventory and Route Validation

**Files:**
- Create: `src/fusion_calling/windows/audio.py`
- Create: `tests/windows/test_audio.py`

**Interfaces:**
- Produces: `AudioEndpoint(index: int, name: str, inputs: int, outputs: int, default_sample_rate: float)`
- Produces: `list_audio_endpoints(query_devices: Callable[[], Sequence[Mapping]]) -> tuple[AudioEndpoint, ...]`
- Produces: `validate_audio_route(endpoints: tuple[AudioEndpoint, ...], input_name: str, output_name: str) -> tuple[AudioEndpoint, AudioEndpoint]`

- [ ] **Step 1: Write failing audio-routing tests**

```python
import pytest

from fusion_calling.windows.audio import list_audio_endpoints, validate_audio_route


def fake_devices():
    return [
        {"name": "CABLE Output", "max_input_channels": 2, "max_output_channels": 0, "default_samplerate": 48000.0},
        {"name": "CABLE Input", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 48000.0},
    ]


def test_route_requires_matching_input_and_output() -> None:
    endpoints = list_audio_endpoints(fake_devices)
    source, sink = validate_audio_route(endpoints, "CABLE Output", "CABLE Input")
    assert source.inputs == 2
    assert sink.outputs == 2


def test_route_fails_when_virtual_device_is_missing() -> None:
    endpoints = list_audio_endpoints(lambda: [])
    with pytest.raises(RuntimeError, match="audio input"):
        validate_audio_route(endpoints, "CABLE Output", "CABLE Input")
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `py -m pytest tests/windows/test_audio.py -v`

Expected: FAIL because `fusion_calling.windows.audio` does not exist.

- [ ] **Step 3: Implement inventory and exact route validation**

Implement the immutable endpoint model and exact route validation:

```python
# src/fusion_calling/windows/audio.py
from collections.abc import Callable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict


class AudioEndpoint(BaseModel):
    model_config = ConfigDict(frozen=True)
    index: int
    name: str
    inputs: int
    outputs: int
    default_sample_rate: float


def list_audio_endpoints(query_devices: Callable[[], Sequence[Mapping]]) -> tuple[AudioEndpoint, ...]:
    return tuple(
        AudioEndpoint(
            index=index,
            name=str(device["name"]).strip(),
            inputs=int(device["max_input_channels"]),
            outputs=int(device["max_output_channels"]),
            default_sample_rate=float(device["default_samplerate"]),
        )
        for index, device in enumerate(query_devices())
    )


def validate_audio_route(
    endpoints: tuple[AudioEndpoint, ...], input_name: str, output_name: str
) -> tuple[AudioEndpoint, AudioEndpoint]:
    source = next((item for item in endpoints if item.name.casefold() == input_name.strip().casefold()), None)
    if source is None or source.inputs == 0 or source.default_sample_rate < 16000:
        raise RuntimeError(f"audio input is unavailable: {input_name}")
    sink = next((item for item in endpoints if item.name.casefold() == output_name.strip().casefold()), None)
    if sink is None or sink.outputs == 0 or sink.default_sample_rate < 16000:
        raise RuntimeError(f"audio output is unavailable: {output_name}")
    return source, sink
```

- [ ] **Step 4: Run the audio tests**

Run: `py -m pytest tests/windows/test_audio.py -v`

Expected: 2 tests PASS.

- [ ] **Step 5: Commit audio validation**

```powershell
git add src/fusion_calling/windows/audio.py tests/windows/test_audio.py
git commit -m "feat: validate Windows audio routes"
```

### Task 5: Read-Only SpokePhone Window Inspection

**Files:**
- Create: `src/fusion_calling/windows/spoke.py`
- Create: `tests/windows/test_spoke.py`

**Interfaces:**
- Produces: `SpokeWindow(title: str, process_id: int, visible: bool, enabled: bool)`
- Produces: `inspect_spoke(desktop: DesktopLike, title_pattern: str) -> SpokeWindow`
- The adapter must not click, type, focus, dial, hang up, or change SpokePhone settings.

- [ ] **Step 1: Write failing read-only inspection tests**

```python
import pytest

from fusion_calling.windows.spoke import inspect_spoke


class FakeWindow:
    def window_text(self): return "Spoke Phone 10.18.0"
    def process_id(self): return 4242
    def is_visible(self): return True
    def is_enabled(self): return True


class FakeDesktop:
    def windows(self, title_re): return [FakeWindow()]


def test_inspect_spoke_returns_window_metadata() -> None:
    result = inspect_spoke(FakeDesktop(), "Spoke Phone")
    assert result.process_id == 4242
    assert result.visible is True


def test_inspect_spoke_fails_on_multiple_windows() -> None:
    class DuplicateDesktop(FakeDesktop):
        def windows(self, title_re): return [FakeWindow(), FakeWindow()]
    with pytest.raises(RuntimeError, match="exactly one"):
        inspect_spoke(DuplicateDesktop(), "Spoke Phone")
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `py -m pytest tests/windows/test_spoke.py -v`

Expected: FAIL because `fusion_calling.windows.spoke` does not exist.

- [ ] **Step 3: Implement strict read-only discovery**

Implement strict discovery without importing or calling any control action:

```python
# src/fusion_calling/windows/spoke.py
import re
from typing import Protocol

from pydantic import BaseModel, ConfigDict


class WindowLike(Protocol):
    def window_text(self) -> str: ...
    def process_id(self) -> int: ...
    def is_visible(self) -> bool: ...
    def is_enabled(self) -> bool: ...


class DesktopLike(Protocol):
    def windows(self, title_re: str) -> list[WindowLike]: ...


class SpokeWindow(BaseModel):
    model_config = ConfigDict(frozen=True)
    title: str
    process_id: int
    visible: bool
    enabled: bool


def inspect_spoke(desktop: DesktopLike, title_pattern: str) -> SpokeWindow:
    windows = desktop.windows(title_re=f".*{re.escape(title_pattern)}.*")
    if len(windows) != 1:
        raise RuntimeError(f"expected exactly one SpokePhone window; found {len(windows)}")
    window = windows[0]
    return SpokeWindow(
        title=window.window_text(),
        process_id=window.process_id(),
        visible=window.is_visible(),
        enabled=window.is_enabled(),
    )
```

- [ ] **Step 4: Run the Spoke inspection tests**

Run: `py -m pytest tests/windows/test_spoke.py -v`

Expected: 2 tests PASS.

- [ ] **Step 5: Commit the Spoke inspector**

```powershell
git add src/fusion_calling/windows/spoke.py tests/windows/test_spoke.py
git commit -m "feat: inspect SpokePhone read only"
```

### Task 6: Read-Only CLI and Lenovo Acceptance Run

**Files:**
- Create: `src/fusion_calling/cli.py`
- Create: `src/fusion_calling/windows/powershell.py`
- Create: `tests/test_cli.py`
- Create: `docs/runbooks/lenovo-foundation.md`

**Interfaces:**
- Produces console commands: `fusion-calling preflight`, `fusion-calling audio-list`, `fusion-calling spoke-inspect`
- Consumes: `collect_preflight`, `list_audio_endpoints`, and `inspect_spoke`
- No command in this phase accepts a telephone number or performs a dial.

- [ ] **Step 1: Write failing CLI tests**

```python
from typer.testing import CliRunner

from fusion_calling.cli import app


runner = CliRunner()


def test_help_exposes_only_read_only_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "preflight" in result.stdout
    assert "audio-list" in result.stdout
    assert "spoke-inspect" in result.stdout
    assert "dial" not in result.stdout.lower()
```

- [ ] **Step 2: Run the CLI test and verify it fails**

Run: `py -m pytest tests/test_cli.py -v`

Expected: FAIL because `fusion_calling.cli` does not exist.

- [ ] **Step 3: Implement the PowerShell runner and CLI**

Implement a fixed-script PowerShell runner; it must not accept script text from CLI input:

```python
# src/fusion_calling/windows/powershell.py
import json
import subprocess


INVENTORY_SCRIPT = r"""
$spoke = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*,HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* -ErrorAction SilentlyContinue |
  Where-Object { $_.DisplayName -like 'Spoke Phone*' } | Select-Object -First 1
$chrome = Get-Item "$env:ProgramFiles\Google\Chrome\Application\chrome.exe" -ErrorAction SilentlyContinue
[ordered]@{
  computer_name = $env:COMPUTERNAME
  windows_build = (Get-CimInstance Win32_OperatingSystem).BuildNumber
  spoke_version = $spoke.DisplayVersion
  chrome_version = if ($chrome) { $chrome.VersionInfo.FileVersion } else { $null }
  audio_devices = @(Get-CimInstance Win32_SoundDevice | ForEach-Object {
    [ordered]@{ name = $_.Name; kind = 'sound'; status = $_.Status }
  })
} | ConvertTo-Json -Depth 4 -Compress
"""


class PowerShellRunner:
    def powershell_json(self, script: str) -> dict:
        if script != "Get Fusion workstation inventory":
            raise ValueError("unsupported PowerShell request")
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", INVENTORY_SCRIPT],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"PowerShell inventory failed: {result.stderr.strip()}")
        if not result.stdout.strip():
            raise RuntimeError("PowerShell inventory returned no data")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError("PowerShell inventory returned invalid JSON") from error
```

Implement the read-only Typer commands:

```python
# src/fusion_calling/cli.py
import json

import sounddevice
import typer
from pywinauto import Desktop

from fusion_calling.windows.audio import list_audio_endpoints
from fusion_calling.windows.powershell import PowerShellRunner
from fusion_calling.windows.preflight import collect_preflight
from fusion_calling.windows.spoke import inspect_spoke


app = typer.Typer(no_args_is_help=True)


@app.command()
def preflight() -> None:
    report = collect_preflight(PowerShellRunner())
    if not report.spoke_version or not report.chrome_version or not any(d.status == "OK" for d in report.audio_devices):
        raise typer.Exit(code=1)
    typer.echo(report.model_dump_json(indent=2))


@app.command("audio-list")
def audio_list() -> None:
    endpoints = list_audio_endpoints(sounddevice.query_devices)
    typer.echo(json.dumps([item.model_dump() for item in endpoints], indent=2))


@app.command("spoke-inspect")
def spoke_inspect() -> None:
    window = inspect_spoke(Desktop(backend="uia"), "Spoke Phone")
    typer.echo(window.model_dump_json(indent=2))
```

- [ ] **Step 4: Write the runbook**

Document these exact Lenovo commands:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
fusion-calling preflight
fusion-calling audio-list
fusion-calling spoke-inspect
py -m pytest -q
```

The runbook must state that Phase 1 cannot place calls, that `dialing_enabled` remains false, and that installing a virtual-audio driver requires a separate confirmation because it changes Windows drivers and may require a restart.

- [ ] **Step 5: Run the complete local test suite**

Run: `py -m pytest -q`

Expected: all tests PASS and no test opens SpokePhone or a browser.

- [ ] **Step 6: Run the read-only commands on the Lenovo**

Run the three CLI commands through the existing SSH connection. Expected evidence:

- Computer name `Joel`
- Windows build `26200`
- Spoke Phone version `10.18.0`
- Chrome detected
- Realtek and Intel audio devices listed as healthy
- Exactly one visible SpokePhone window after Joel opens the application
- No calls, texts, appointments, tasks, notes, or CRM changes

- [ ] **Step 7: Commit the Phase 1 deliverable**

```powershell
git add src/fusion_calling/cli.py src/fusion_calling/windows/powershell.py tests/test_cli.py docs/runbooks/lenovo-foundation.md
git commit -m "feat: add Lenovo foundation diagnostics"
```

## Phase 1 Exit Criteria

Phase 1 is complete only when:

1. The full test suite passes on the Lenovo.
2. All three CLI commands return expected read-only evidence.
3. Dialing remains disabled and no dial command exists.
4. No Zoho record or Outlook/Bookings appointment has changed.
5. Joel reviews the evidence before authorizing the separate voice-and-internal-call phase.
