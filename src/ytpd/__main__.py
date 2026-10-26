import uvicorn

from ytpd.application_composer import ApplicationComposer


def main() -> None:
    """Compose the application and serve it on the configured localhost bind."""
    composed = ApplicationComposer().compose()
    if composed.gil_warning is not None:
        print(composed.gil_warning)
    settings = composed.settings
    print(f"Serving on http://{settings.host}:{settings.port}")
    uvicorn.run(
        composed.app,
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
