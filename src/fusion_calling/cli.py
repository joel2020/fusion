import json

import sounddevice
import typer

from fusion_calling.windows.audio import list_audio_endpoints
from fusion_calling.windows.powershell import PowerShellRunner
from fusion_calling.windows.preflight import collect_preflight
from fusion_calling.windows.spoke import inspect_spoke


app = typer.Typer(no_args_is_help=True)


@app.command()
def preflight() -> None:
    report = collect_preflight(PowerShellRunner())
    if (
        not report.spoke_version
        or not report.chrome_version
        or not any(device.status == "OK" for device in report.audio_devices)
    ):
        raise typer.Exit(code=1)
    typer.echo(report.model_dump_json(indent=2))


@app.command("audio-list")
def audio_list() -> None:
    endpoints = list_audio_endpoints(sounddevice.query_devices)
    typer.echo(json.dumps([item.model_dump() for item in endpoints], indent=2))


@app.command("spoke-inspect")
def spoke_inspect() -> None:
    from pywinauto import Desktop

    window = inspect_spoke(Desktop(backend="uia"), "Spoke Phone")
    typer.echo(window.model_dump_json(indent=2))
