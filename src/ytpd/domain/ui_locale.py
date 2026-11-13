from enum import Enum


class UiLocale(Enum):
    """Supported UI languages persisted in application config."""

    EN = "en"
    FR = "fr"

    @classmethod
    def parse(cls, raw: str) -> "UiLocale":
        """Parse a locale code; raise ``ValueError`` when unsupported."""
        normalized = raw.strip().casefold()
        for member in cls:
            if member.value == normalized:
                return member
        allowed = ", ".join(member.value for member in cls)
        raise ValueError(f"ui_locale must be one of: {allowed}")

    @classmethod
    def codes(cls) -> list[str]:
        """Return locale codes in enum definition order."""
        return [member.value for member in cls]
