---
description: Architecture rules for Django — SOLID principles, design patterns, and app conventions
---

# WJS Django Architecture Rules

> **Note for anyone porting rules from another `wjs-*` repo:** this repo (`wjs-themes`) is a
> themes/templates package plus a small standalone admin app — it has no submission workflow, no
> step forms, no `RevisionStorage`, and no business-logic classes of the kind described in
> `wjs-submission-project`'s architecture rules. Don't port that file's *Model*/*Forms*/*Business
> logic*/*Views* sections here; they describe a different repo. What follows is this repo's own
> architecture.

## SOLID principles

- **Single Responsibility**: one class/module = one concern
- **Open/Closed**: extend via subclassing or registry, not by editing core code
- **Liskov Substitution**: subclasses must honour parent contracts
- **Interface Segregation**: small focused interfaces over fat ones
- **Dependency Inversion**: depend on abstractions; inject concrete implementations

## What this repo actually contains

This package has no models and (almost) no forms/views of its own — it plugs presentation and a
curated admin surface into an existing Janeway installation:

- **`wjs/themes/apps.py::WJSThemesConfig`** — declares the theme names (`themes = ("wjs-bootstrap",
  "JCOM-theme")`) and, in `ready()`, appends `wjs-bootstrap/templates` to Django's global
  `TEMPLATES[0]["DIRS"]`. This is a deliberate exception to the usual "app templates live under
  `templates/<app_name>/`, never globally" convention (see `.claude/rules/templates-django.md`):
  wjs-bootstrap must be reachable even for journals that have a *different* theme selected,
  because other wjs apps (e.g. wjs-review) extend its templates directly.
- **`wjs/themes/management/commands/install_themes.py`** — the extension point for adding a theme:
  it iterates `WJSThemesConfig.themes` and symlinks each into Janeway's `themes/` folder, and
  applies `wjs/install/settings.json` via Janeway's `update_settings`. Adding a new theme means
  adding its name to `WJSThemesConfig.themes`, not writing new install logic.
- **`wjs/themes/wjs-bootstrap/build_assets.py` / `wjs/themes/JCOM-theme/build_assets.py`** — each
  theme's asset pipeline, matching Janeway's `manage.py build_assets` contract (a module-level
  `build()` function). wjs-bootstrap's explicitly lists every compiled CSS entry point in
  `THEME_CSS_FILES` — one per journal — so adding a journal-specific stylesheet means adding it to
  that list, not just dropping a `.scss` file in `assets/sass/`.
- **`wjs/advanced_admin/`** — a second, separate `AdminSite` (`AdvancedAdminSite` in
  `admin_site.py`), not the default Django admin. `admin.py` registers a curated subset of
  Janeway's own models (`File`, `SupplementaryFile`, `XSLFile`, `Article`, `GalleyProofing`)
  against it with custom `ModelAdmin`s — restricted `has_add_permission`, computed `list_display`
  columns (e.g. `ArticleAdmin.state`/`pubid`), and (for `FileAdmin`) a custom `ModelForm`
  (`FileForm`) whose `save()` handles the uploaded-file-to-article-path logic directly, since
  there is no separate forms/business-logic layer here to delegate to.
- **`wjs/themes/context_processors.py`** — the one piece of cross-cutting app logic, injecting
  `WJS_THEMES_VERSION` into every template's context.

Prefer following these existing shapes over introducing new patterns (e.g. a `logic.py` business
class, a step-form pipeline) that belong to `wjs-submission-project`'s domain, not this one.

## Registry / Decorator pattern

Prefer registries over direct imports for extensible, plugin-like behaviour. Components
register themselves; core code iterates the registry rather than importing each component. In
this repo, `WJSThemesConfig.themes` and `admin.register(..., site=advanced_admin_site)` are the
existing examples of this — add to them rather than hand-rolling equivalent wiring.

## Dependency Injection

Pass dependencies into constructors or factory functions. Avoid module-level singletons
and global state that makes testing and substitution difficult.

## Reusable packages vs project code

- Reusable logic → extract to a `nephila-apps` / `nephila-widgets` package with its own
  towncrier changelog and semver versioning
- Project-specific logic → keep in the project app; do not prematurely extract
- The boundary: if two unrelated projects need the same code, it belongs in a package

## Dependency selection

- Always verify the compatibility of the selected library with the project
- Avoid using libraries that are not actively maintained
- Prefer libraries with a permissive license (MIT, Apache, BSD, etc.)
