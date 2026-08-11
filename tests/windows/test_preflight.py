from fusion_calling.windows.preflight import collect_preflight


class FakeRunner:
    def powershell_json(self, script: str) -> dict:
        return {
            "computer_name": "Joel",
            "windows_build": "26200",
            "spoke_version": "10.18.0",
            "chrome_version": "151.0.7922.138",
            "audio_devices": [
                {
                    "name": "Realtek High Definition Audio(SST)",
                    "kind": "sound",
                    "status": "OK",
                }
            ],
        }


def test_collect_preflight_maps_inventory() -> None:
    report = collect_preflight(FakeRunner())

    assert report.computer_name == "Joel"
    assert report.windows_build == "26200"
    assert report.spoke_version == "10.18.0"
    assert report.audio_devices[0].status == "OK"
    assert report.errors == ()
