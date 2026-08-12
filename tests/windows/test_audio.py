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


def test_route_rejects_missing_output() -> None:
    endpoints = list_audio_endpoints(fake_devices)

    with pytest.raises(RuntimeError, match="audio output"):
        validate_audio_route(endpoints, "CABLE Output", "Missing Cable Input")


@pytest.mark.parametrize("outputs", [0, -1])
def test_route_rejects_non_positive_output_channels(outputs: int) -> None:
    endpoints = list_audio_endpoints(
        lambda: [
            {
                "name": "CABLE Output",
                "max_input_channels": 2,
                "max_output_channels": 0,
                "default_samplerate": 48000.0,
            },
            {
                "name": "CABLE Input",
                "max_input_channels": 0,
                "max_output_channels": outputs,
                "default_samplerate": 48000.0,
            },
        ]
    )

    with pytest.raises(RuntimeError, match="audio output"):
        validate_audio_route(endpoints, "CABLE Output", "CABLE Input")


@pytest.mark.parametrize("inputs", [0, -1])
def test_route_rejects_non_positive_input_channels(inputs: int) -> None:
    endpoints = list_audio_endpoints(
        lambda: [
            {
                "name": "CABLE Output",
                "max_input_channels": inputs,
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
    )

    with pytest.raises(RuntimeError, match="audio input"):
        validate_audio_route(endpoints, "CABLE Output", "CABLE Input")


@pytest.mark.parametrize("sample_rate", [15999.0, float("nan"), float("inf")])
def test_route_rejects_invalid_input_sample_rate(sample_rate: float) -> None:
    endpoints = list_audio_endpoints(
        lambda: [
            {
                "name": "CABLE Output",
                "max_input_channels": 2,
                "max_output_channels": 0,
                "default_samplerate": sample_rate,
            },
            {
                "name": "CABLE Input",
                "max_input_channels": 0,
                "max_output_channels": 2,
                "default_samplerate": 48000.0,
            },
        ]
    )

    with pytest.raises(RuntimeError, match="audio input"):
        validate_audio_route(endpoints, "CABLE Output", "CABLE Input")


@pytest.mark.parametrize("sample_rate", [15999.0, float("nan"), float("inf")])
def test_route_rejects_invalid_output_sample_rate(sample_rate: float) -> None:
    endpoints = list_audio_endpoints(
        lambda: [
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
                "default_samplerate": sample_rate,
            },
        ]
    )

    with pytest.raises(RuntimeError, match="audio output"):
        validate_audio_route(endpoints, "CABLE Output", "CABLE Input")


def test_route_matches_names_case_insensitively_after_trimming() -> None:
    endpoints = list_audio_endpoints(fake_devices)

    source, sink = validate_audio_route(endpoints, " cable output ", " cable input ")

    assert source.name == "CABLE Output"
    assert sink.name == "CABLE Input"
