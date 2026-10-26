import pytest

from ytpd.config.bind_settings_loader import BindSettingsLoader
from ytpd.config.invalid_bind_settings_error import InvalidBindSettingsError


def test_loads_packaged_default_settings() -> None:
    settings = BindSettingsLoader().load_default()
    assert settings.host == "127.0.0.1"
    assert settings.port == 8765


def test_loads_valid_bind_settings_from_text() -> None:
    settings = BindSettingsLoader().load_text(
        'bind_host: "127.0.0.1"\nbind_port: 8765\n'
    )
    assert settings.host == "127.0.0.1"
    assert settings.port == 8765


def test_rejects_non_integer_port() -> None:
    with pytest.raises(InvalidBindSettingsError):
        BindSettingsLoader().load_text(
            'bind_host: "127.0.0.1"\nbind_port: "nope"\n'
        )


def test_rejects_bool_port() -> None:
    with pytest.raises(InvalidBindSettingsError):
        BindSettingsLoader().load_text(
            'bind_host: "127.0.0.1"\nbind_port: true\n'
        )


def test_rejects_non_mapping_root() -> None:
    with pytest.raises(InvalidBindSettingsError):
        BindSettingsLoader().load_text("- just a list\n")
