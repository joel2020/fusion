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
