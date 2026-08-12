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
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                INVENTORY_SCRIPT,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"PowerShell inventory failed: {result.stderr.strip()}"
            )
        if not result.stdout.strip():
            raise RuntimeError("PowerShell inventory returned no data")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError("PowerShell inventory returned invalid JSON") from error
