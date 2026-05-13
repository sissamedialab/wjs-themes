"""Configure this application."""

import os
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings


class WJSThemesConfig(AppConfig):
    """Configuration for this django app."""

    name = "wjs.themes"
    verbose_name = "WJS Themes"
    path = str(Path(__file__).parent.absolute())
    themes = (
        "wjs-bootstrap",
        "JCOM-theme",
    )

    def ready(self):
        """
        Inject wjs-bootstrap templates into templates DIRS to make it available independently from selected theme.

        wjs-review use wjs-bootstrap as a base and we must make it available globally
        """
        settings.TEMPLATES[0]["DIRS"].append(os.path.join(self.path, "wjs-bootstrap", "templates"))  # noqa: PTH118
