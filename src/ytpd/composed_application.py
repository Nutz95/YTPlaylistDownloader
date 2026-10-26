from dataclasses import dataclass

from fastapi import FastAPI

from ytpd.config.app_config import AppConfig


@dataclass(frozen=True)
class ComposedApplication:
    """Fully wired FastAPI app plus runtime config and optional GIL warning."""

    app: FastAPI
    settings: AppConfig
    gil_warning: str | None
