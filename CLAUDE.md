# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`wjs-themes` is a Django/Janeway **themes package** for the WJS (Workflow for Janeway) project family
(JCOM, JCAP, JHEP, JINST, JQUANT, JSTAT, POS, etc.). It is distributed as a standard Python package
(not a Janeway plugin) so it can be installed independently. It has no standalone runtime of its own —
it only makes sense mounted inside a Janeway installation (`../janeway/src` relative to this repo in
local dev setups), which provides Django, the `core`/`submission`/`typesetting` apps, `manage.py`, etc.
There is no test suite in this repo; behavior is verified inside a running Janeway instance.

It provides two themes plus an "advanced admin" Django app:

- **wjs-bootstrap** (`wjs/themes/wjs-bootstrap/`): the actively developed Bootstrap 5-based theme, used
  both as a Janeway "Journal Theme" and as a plain Django template base for wjs-specific apps (e.g.
  wjs-review). Its templates are injected into Django's global `TEMPLATES[0]["DIRS"]` (see
  `wjs/themes/apps.py::WJSThemesConfig.ready()`), so wjs-bootstrap templates are always available
  regardless of which theme a journal has selected.
- **JCOM-theme** (`wjs/themes/JCOM-theme/`): legacy "Vetrinetta" theme derived from Janeway's `material`
  theme. Only used by journals that explicitly select it; not being actively developed.
- **advanced_admin** (`wjs/advanced_admin/`): a separate Django admin site (`AdvancedAdminSite`) exposing
  a curated subset of Janeway models (`File`, `SupplementaryFile`, `XSLFile`, `Article`, `GalleyProofing`)
  with custom list displays/permissions, mounted at its own URL via `wjs/advanced_admin/urls.py`.

## Repository layout

```
wjs/
  themes/
    apps.py                     # WJSThemesConfig: registers theme names, injects wjs-bootstrap templates globally
    context_processors.py       # exposes WJS_THEMES_VERSION in template context
    management/commands/install_themes.py  # symlinks themes into Janeway's themes/ dir, runs Janeway's update_settings
    wjs-bootstrap/
      assets/sass/              # SCSS sources, one entry-point per journal (wjs_jcom.scss, wjs_jhep.scss, ...)
                                 # plus shared partials (_wjs_base.scss, _badges_colors.scss, ...)
      build_assets.py           # compiles SCSS -> CSS into Janeway's static/wjs-bootstrap/, copies images, collectstatic
      templates/wjs/base/       # base.html + reusable elements/fragments (header, footer, nav, modals, ...)
      templates/                # overrides of Janeway core/journal/cms/forms/hijack templates
    JCOM-theme/
      assets/, fonts/, build_assets.py, templates/   # legacy theme, same pattern as wjs-bootstrap
    locale/{en,es,pt}/LC_MESSAGES/django.po   # translations
  advanced_admin/                # standalone AdminSite + admin.py + urls.py
  install/settings.json          # custom Janeway settings (journal fields) installed via update_settings
```

## Working with a theme's assets (SCSS)

Each journal in wjs-bootstrap has its own SCSS entry point (`wjs_jcom.scss`, `wjs_jcap.scss`,
`wjs_jhep.scss`, `wjs_jinst.scss`, `wjs_jquant.scss`, `wjs_jstat.scss`, `wjs_jcomal.scss`, `wjs_pos.scss`)
plus `base.scss` and `wjs_review.scss`, all listed explicitly in `THEME_CSS_FILES` in
`wjs/themes/wjs-bootstrap/build_assets.py`. **When adding a new journal-specific stylesheet, add it to
`THEME_CSS_FILES` or it will never be compiled.** Shared styles go in the `_`-prefixed partials
(`_wjs_base.scss`, `_badges_colors.scss`, `_submission-authors.scss`, `_submission-keywords.scss`,
`_submission-review-submit.scss`, `_wjs_showcase.scss`) and are `@import`ed by the per-journal entry
points.

`build_assets.py` (per theme) is Janeway's documented theming hook: Janeway's `manage.py build_assets`
calls `build()`, which creates `static/wjs-bootstrap/{css,js,fonts,img}`, compiles each SCSS entry point
via `libsass`, copies `assets/images` into the static img folder, and runs Django's `collectstatic`.

From this repo, `build_assets.sh` drives that loop during development: it assumes a sibling `../janeway`
checkout, runs `python manage.py build_assets` once, then watches (`inotifywait`) the `assets/` dirs of
both themes and re-runs the build on change. Run it from within a Janeway checkout that has this package
installed (editable) alongside it.

## Installing / linking themes into Janeway

`python manage.py install_themes` (Janeway management command provided by this package,
`wjs/themes/management/commands/install_themes.py`) symlinks each theme in `WJSThemesConfig.themes`
(`wjs-bootstrap`, `JCOM-theme`) from this package into Janeway's `themes/` directory, and applies the
journal-setting definitions in `wjs/install/settings.json` via Janeway's `utils.install.update_settings`.
Re-running it is safe/idempotent (it detects an existing correct symlink); a pre-existing non-symlink
path at the destination is reported as an error rather than overwritten.

## Templates conventions

- Extend `wjs/base/base.html` when building a plain Django view on top of wjs-bootstrap (not going
  through Janeway's theme-selection machinery).
- Reusable page chrome lives under `templates/wjs/base/elements/` (header, footer, nav, user menu,
  breadcrumbs, pagination, modals) and `templates/wjs/base/fragments/` (e.g. `mathjax.html`).
- Files directly under `templates/<app>/...` (e.g. `templates/journal/article.html`,
  `templates/core/...`, `templates/cms/page.html`, `templates/hijack/...`) are theme overrides of the
  matching Janeway/core template path — keep the override's template name and block structure aligned
  with the upstream Janeway template it replaces.

## Formatting / linting

Pre-commit (`.pre-commit-config.yaml`) is the source of truth, run in CI via the shared
`wjs-profile-project` pipeline templates (`.gitlab-ci.yml`):

- **ruff** (lint + format) for Python — config in `pyproject.toml`. `select = ["ALL"]` with an explicit
  `ignore` list (docstring rules, annotation rules, boolean-trap rules, magic-value rule, etc. are
  disabled); `line-length = 119`; `preview = true`; isort integration via `extend-select = ["I"]`.
- **djlint** (`djlint-django` profile, `H006` ignored) for Django templates, excluding `*/tests/*.html`.
- **prettier** (pinned to 2.8.0 via the pre-commit mirror) for `.js`/`.jsx`/`.ts`/`.tsx`/`.css`/`.scss` —
  config in `.prettierrc` (120-col, double quotes, no semicolons... see file for exact settings).
- Standard hygiene hooks: trailing whitespace, large files, merge conflicts, YAML/TOML/JSON validity,
  LF line endings.

Run `pre-commit run --all-files` before committing if changing Python, templates, JS, or SCSS.

## Packaging / release

This is a version-controlled Python package (`setup.cfg`, current version tracked there — bump on
release), built with `setuptools`. CI (`.gitlab-ci.yml`) includes shared pipeline definitions from the
`wjs/wjs-profile-project` GitLab project for pre-commit checks, package build/upload (on tags), and
deploy stages to pre-production/production/dev/T1-T5 test environments — deploys run by installing the
already-uploaded package on the target server, so they only make sense after "Upload package" has run
on a tag.
