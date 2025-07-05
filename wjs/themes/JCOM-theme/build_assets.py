"""
Process any SCSS and copy the resulting files into the main static folder.

Or just pass if not required. See
path/to/janeway/src/themes/OLH/build_assets.py as an example.

https://janeway.readthedocs.io/en/latest/configuration.html#theming

"""

import shutil
from pathlib import Path

import sass
from django.conf import settings
from django.core.management import call_command

BASE_THEME_DIR = Path(settings.BASE_DIR) / "static" / "JCOM-theme"
SRC_THEME_DIR = Path(__file__).parent
THEME_CSS_FILES = [
    BASE_THEME_DIR / "css" / "jcom.css",
    BASE_THEME_DIR / "css" / "jcom_nav.css",
    BASE_THEME_DIR / "css" / "jcomal.css",
    BASE_THEME_DIR / "css" / "jcomal_nav.css",
    BASE_THEME_DIR / "css" / "newsletter_jcom.css",
    BASE_THEME_DIR / "css" / "newsletter_jcomal.css",
    BASE_THEME_DIR / "css" / "newsletter_mobile.css",
]


def process_scss():
    """Compiles SCSS into CSS in the Static Assets folder."""
    include_path_materialize = SRC_THEME_DIR / "assets" / "materialize-src" / "sass"
    include_path_bootstrap = SRC_THEME_DIR / "assets"

    for css_file in THEME_CSS_FILES:
        app_scss_file = SRC_THEME_DIR / "assets" / "sass" / f"{css_file.stem}.scss"

        include_path_jcom = app_scss_file.parent
        compiled_css_from_file = sass.compile(
            filename=str(app_scss_file),
            include_paths=[
                str(include_path_jcom),
                str(include_path_materialize),
                str(include_path_bootstrap),
            ],
        )

        # Open the CSS file and write into it
        with css_file.open("w", encoding="utf-8") as write_file:
            write_file.write(compiled_css_from_file)


def create_paths():
    """Create destination dirs for css & co."""
    folders = [
        "css",
        "js",
        "fonts",
        "img",
    ]

    for folder in folders:
        (BASE_THEME_DIR / folder).mkdir(parents=True, exist_ok=True)
    return BASE_THEME_DIR / "css"


def build():
    """Build assets and copy them to static folder."""
    print("JCOM SCSS START")
    create_paths()
    print("JCOM PATHS DONE")
    process_scss()
    print("JCOM SCSS DONE")
    copy_file(
        "themes/JCOM-theme/assets/materialize-src/fonts",
        "static/JCOM-theme/fonts",
        False,
    )
    copy_file(
        "themes/JCOM-theme/assets/materialize-src/js/bin/materialize.min.js",
        "static/JCOM-theme/js/materialize.min.js",
    )
    call_command("collectstatic", "--noinput")
    print("JCOM collectstatic DONE")


def copy_file(source, destination, is_file=True):
    """
    Copy files to Janeway's themes directory.

    :param source: The source of the folder for copying
    :param destination: The destination folder for the file
    :return:
    """
    base_dir = Path(settings.BASE_DIR)
    destination_path = base_dir / destination
    destination_folder = destination_path.parent

    if is_file:
        if not destination_folder.exists():
            destination_folder.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            base_dir / source,
            destination_path,
        )
    else:
        shutil.copytree(
            base_dir / source,
            destination_path,
            dirs_exist_ok=True,
        )
