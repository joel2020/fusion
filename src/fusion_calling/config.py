from pathlib import Path
import tomllib

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class CallingConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    dialing_enabled: bool = False
    allowed_test_numbers: tuple[str, ...] = ()
    spoke_window_pattern: str = "Spoke Phone"

    @field_validator("allowed_test_numbers")
    @classmethod
    def normalize_numbers(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = []
        for value in values:
            digits = "".join(character for character in value if character.isdigit())
            if len(digits) == 10:
                digits = "1" + digits
            if len(digits) != 11 or not digits.startswith("1"):
                raise ValueError("test numbers must be valid US numbers")
            normalized.append("+" + digits)
        return tuple(normalized)

    @model_validator(mode="after")
    def require_allowlist_when_enabled(self) -> "CallingConfig":
        if self.dialing_enabled and not self.allowed_test_numbers:
            raise ValueError("allowed_test_numbers is required when dialing is enabled")
        return self

    @classmethod
    def load(cls, path: Path) -> "CallingConfig":
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
        return cls.model_validate(payload.get("workstation", {}))
