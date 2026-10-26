from ytpd.composed_application import ComposedApplication
from ytpd.config.app_config_store import AppConfigStore
from ytpd.config.path_validator import PathValidator
from ytpd.config.writable_config_path import WritableConfigPath
from ytpd.runtime.python_version_guard import PythonVersionGuard
from ytpd.runtime.sys_interpreter_version_provider import SysInterpreterVersionProvider
from ytpd.web.app_factory import AppFactory
from ytpd.web.static_directory import StaticDirectory
from ytpd.web.template_directory import TemplateDirectory


class ApplicationComposer:
    """Composition root that wires runtime checks, settings, and the web app."""

    def compose(self) -> ComposedApplication:
        """Build a ready-to-serve application with config and GIL warning."""
        gil_warning = PythonVersionGuard().check(
            SysInterpreterVersionProvider().read()
        )
        config_store = AppConfigStore(
            WritableConfigPath().resolve(),
            PathValidator(),
        )
        config = config_store.load()
        app = AppFactory(
            TemplateDirectory().resolve(),
            StaticDirectory().resolve(),
            config,
            config_store,
        ).build()
        return ComposedApplication(
            app=app,
            settings=config,
            gil_warning=gil_warning,
        )
