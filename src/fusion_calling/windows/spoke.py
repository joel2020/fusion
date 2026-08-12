"""Read-only SpokePhone window discovery."""

import re
from typing import Protocol

from pydantic import BaseModel, ConfigDict


class WindowLike(Protocol):
    def window_text(self) -> str: ...

    def process_id(self) -> int: ...

    def is_visible(self) -> bool: ...

    def is_enabled(self) -> bool: ...


class DesktopLike(Protocol):
    def windows(self, title_re: str) -> list[WindowLike]: ...


class SpokeWindow(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    process_id: int
    visible: bool
    enabled: bool


def inspect_spoke(desktop: DesktopLike, title_pattern: str) -> SpokeWindow:
    """Return metadata for the sole SpokePhone window matching ``title_pattern``."""
    windows = desktop.windows(title_re=f".*{re.escape(title_pattern)}.*")
    if len(windows) != 1:
        raise RuntimeError(f"expected exactly one SpokePhone window; found {len(windows)}")

    window = windows[0]
    return SpokeWindow(
        title=window.window_text(),
        process_id=window.process_id(),
        visible=window.is_visible(),
        enabled=window.is_enabled(),
    )
