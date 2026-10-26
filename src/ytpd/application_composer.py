from ytpd.composed_application import ComposedApplication
from ytpd.config.bind_settings_loader import BindSettingsLoader
from ytpd.runtime.python_version_guard import PythonVersionGuard
from ytpd.runtime.sys_interpreter_version_provider import SysInterpreterVersionProvider
from ytpd.web.app_factory import AppFactory
from ytpd.web.template_directory import TemplateDirectory


class ApplicationComposer:
    """Composition root that wires runtime checks, settings, and the web app."""

    def compose(self) -> ComposedApplication:
        """Build a ready-to-serve application with bind settings and GIL warning."""
        gil_warning = PythonVersionGuard().check(
            SysInterpreterVersionProvider().read()
        )
        settings = BindSettingsLoader().load_default()
        templates_dir = TemplateDirectory().resolve()
        app = AppFactory(templates_dir).build()
        return ComposedApplication(
            app=app,
            settings=settings,
            gil_warning=gil_warning,
        )
