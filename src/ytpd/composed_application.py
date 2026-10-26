from dataclasses import dataclass

from fastapi import FastAPI

from ytpd.config.bind_settings import BindSettings


@dataclass(frozen=True)
class ComposedApplication:
    """Fully wired FastAPI app plus bind settings and optional GIL warning."""

    app: FastAPI
    settings: BindSettings
    gil_warning: str | None
