from dataclasses import dataclass, field
from threading import Lock

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
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def acquire(self, call_id: str) -> None:
        with self._lock:
            if self.active_call_id is not None:
                raise RuntimeError("a call is already active")
            self.active_call_id = call_id

    def release(self, call_id: str) -> None:
        with self._lock:
            if self.active_call_id != call_id:
                raise RuntimeError("call id does not own the interlock")
            self.active_call_id = None
