from pathlib import Path

import pytest

from fusion_calling.config import CallingConfig


def test_defaults_disable_dialing(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[workstation]\nspoke_window_pattern = "Spoke Phone"\n')
    config = CallingConfig.load(path)
    assert config.dialing_enabled is False
    assert config.allowed_test_numbers == ()


def test_enabled_dialing_requires_test_number(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        '[workstation]\ndialing_enabled = true\nspoke_window_pattern = "Spoke Phone"\n'
    )
    with pytest.raises(ValueError, match="allowed_test_numbers"):
        CallingConfig.load(path)
