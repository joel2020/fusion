import pytest

from fusion_calling.windows.spoke import inspect_spoke


class FakeWindow:
    def window_text(self) -> str:
        return "Spoke Phone 10.18.0"

    def process_id(self) -> int:
        return 4242

    def is_visible(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        return True


class FakeDesktop:
    def windows(self, title_re: str) -> list[FakeWindow]:
        return [FakeWindow()]


def test_inspect_spoke_returns_window_metadata() -> None:
    result = inspect_spoke(FakeDesktop(), "Spoke Phone")

    assert result.title == "Spoke Phone 10.18.0"
    assert result.process_id == 4242
    assert result.visible is True
    assert result.enabled is True


def test_inspect_spoke_fails_on_multiple_windows() -> None:
    class DuplicateDesktop(FakeDesktop):
        def windows(self, title_re: str) -> list[FakeWindow]:
            return [FakeWindow(), FakeWindow()]

    with pytest.raises(RuntimeError, match="exactly one"):
        inspect_spoke(DuplicateDesktop(), "Spoke Phone")


def test_inspect_spoke_fails_when_no_windows_match() -> None:
    class NoWindowDesktop(FakeDesktop):
        def windows(self, title_re: str) -> list[FakeWindow]:
            return []

    with pytest.raises(RuntimeError, match="exactly one"):
        inspect_spoke(NoWindowDesktop(), "Spoke Phone")
