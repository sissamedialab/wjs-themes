"""Install all custom themes into Janeway."""

from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Install custom themes into Janeway."

    def handle(self, *args, **options):
        """Command entry point."""
        destination_folder = (Path(settings.BASE_DIR) / "themes").resolve()
        config = apps.get_app_config("themes")
        themes_folder = config.path
        for theme in config.themes:
            destination = destination_folder / theme
            self.stdout.write(
                self.style.SUCCESS(f"Linking {theme} to {destination}..."),
            )
            theme_folder = themes_folder / theme
            try:
                destination.symlink_to(theme_folder)
            except FileExistsError:
                if destination.readlink() == theme_folder:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "...link to theme already there, nothing to do.",
                        ),
                    )
                else:
                    self.stderr.write(
                        self.style.ERROR("...different file exists! Please check."),
                    )
                    self.stderr.write(
                        self.style.ERROR(
                            f"{theme_folder} VS {destination.readlink()}",
                        ),
                    )
            else:
                self.stdout.write(self.style.SUCCESS("...done."))
