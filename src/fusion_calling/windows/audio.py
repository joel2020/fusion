from collections.abc import Callable, Mapping, Sequence
from math import isfinite

from pydantic import BaseModel, ConfigDict


class AudioEndpoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    index: int
    name: str
    inputs: int
    outputs: int
    default_sample_rate: float


def list_audio_endpoints(
    query_devices: Callable[[], Sequence[Mapping]],
) -> tuple[AudioEndpoint, ...]:
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
    source = next(
        (item for item in endpoints if item.name.casefold() == input_name.strip().casefold()),
        None,
    )
    if (
        source is None
        or source.inputs <= 0
        or not isfinite(source.default_sample_rate)
        or source.default_sample_rate < 16000
    ):
        raise RuntimeError(f"audio input is unavailable: {input_name}")

    sink = next(
        (item for item in endpoints if item.name.casefold() == output_name.strip().casefold()),
        None,
    )
    if (
        sink is None
        or sink.outputs <= 0
        or not isfinite(sink.default_sample_rate)
        or sink.default_sample_rate < 16000
    ):
        raise RuntimeError(f"audio output is unavailable: {output_name}")

    return source, sink
