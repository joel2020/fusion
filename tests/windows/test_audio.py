import pytest

from fusion_calling.windows.audio import list_audio_endpoints, validate_audio_route


def fake_devices():
    return [
        {
            "name": "CABLE Output",
            "max_input_channels": 2,
            "max_output_channels": 0,
            "default_samplerate": 48000.0,
        },
        {
            "name": "CABLE Input",
            "max_input_channels": 0,
            "max_output_channels": 2,
            "default_samplerate": 48000.0,
        },
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
