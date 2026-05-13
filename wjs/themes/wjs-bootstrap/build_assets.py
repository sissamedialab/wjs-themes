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

BASE_THEME_DIR = Path(settings.BASE_DIR) / "static" / "wjs-bootstrap"
SRC_THEME_DIR = Path(__file__).parent
THEME_CSS_FILES = [
    BASE_THEME_DIR / "css" / "base.css",
    BASE_THEME_DIR / "css" / "wjs_review.css",
    BASE_THEME_DIR / "css" / "wjs_jcap.css",
    BASE_THEME_DIR / "css" / "wjs_jcom.css",
    BASE_THEME_DIR / "css" / "wjs_jcomal.css",
    BASE_THEME_DIR / "css" / "wjs_jhep.css",
    BASE_THEME_DIR / "css" / "wjs_jinst.css",
    BASE_THEME_DIR / "css" / "wjs_jquant.css",
    BASE_THEME_DIR / "css" / "wjs_jstat.css",
    BASE_THEME_DIR / "css" / "wjs_pos.css",
]


def process_scss():
    """Compiles SCSS into CSS in the Static Assets folder."""
    include_path_bootstrap = SRC_THEME_DIR / "assets"

    for css_file in THEME_CSS_FILES:
        app_scss_file = SRC_THEME_DIR / "assets" / "sass" / f"{css_file.stem}.scss"

        include_custom_style = app_scss_file.parent
        compiled_css_from_file = sass.compile(
            filename=str(app_scss_file),
            include_paths=[
                str(include_custom_style),
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
    print("THEMES SCSS START")
    create_paths()
    print("THEMES PATHS DONE")
    process_scss()
    print("THEMES SCSS DONE")
    copy_file(
        source="themes/wjs-bootstrap/assets/images",
        destination="static/wjs-bootstrap/img",
        is_file=False,
    )
    call_command("collectstatic", "--noinput")
    print("THEMES collectstatic DONE")


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
