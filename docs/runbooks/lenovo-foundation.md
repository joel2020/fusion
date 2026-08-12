# Lenovo Calling Foundation Acceptance Run

Phase 1 is read-only and cannot place calls. It exposes diagnostics only; there
is no dial command, and `dialing_enabled` remains `false`.

For a long, explicitly authorized acceptance run while the Lenovo is connected
to AC power, prevent sleep and hibernation without changing battery settings:

```powershell
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /getactivescheme
powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE
powercfg /query SCHEME_CURRENT SUB_SLEEP HIBERNATEIDLE
```

These settings apply only to AC power; do not alter the corresponding DC
settings.

From the dedicated repository folder on the Lenovo, run:

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

Open Spoke Phone before `spoke-inspect`. The command reads metadata for the
single matching visible application window; it does not operate the interface.

Do not install a virtual-audio driver during this acceptance run. Installing
one changes Windows drivers and may require a restart, so it requires separate
confirmation.
