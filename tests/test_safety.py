from threading import Barrier, Thread

import pytest

from fusion_calling.config import CallingConfig
from fusion_calling.safety import CallInterlock, DialSafetyGate, normalize_us_number


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


def test_normalize_us_number_rejects_non_us_number() -> None:
    with pytest.raises(ValueError, match="valid US number"):
        normalize_us_number("44 20 7946 0018")


def test_interlock_rejects_second_active_call() -> None:
    interlock = CallInterlock()
    interlock.acquire("call-1")

    with pytest.raises(RuntimeError, match="already active"):
        interlock.acquire("call-2")

    interlock.release("call-1")


def test_interlock_rejects_release_by_non_owner() -> None:
    interlock = CallInterlock()
    interlock.acquire("call-1")

    with pytest.raises(RuntimeError, match="does not own"):
        interlock.release("call-2")


def test_interlock_allows_exactly_one_concurrent_acquisition() -> None:
    interlock = CallInterlock()
    start = Barrier(3)
    outcomes: list[str] = []

    def acquire(call_id: str) -> None:
        start.wait()
        try:
            interlock.acquire(call_id)
        except RuntimeError as error:
            outcomes.append(str(error))
        else:
            outcomes.append(call_id)

    first = Thread(target=acquire, args=("call-1",))
    second = Thread(target=acquire, args=("call-2",))
    first.start()
    second.start()
    start.wait()
    first.join()
    second.join()

    assert sum(outcome in {"call-1", "call-2"} for outcome in outcomes) == 1
    assert outcomes.count("a call is already active") == 1
