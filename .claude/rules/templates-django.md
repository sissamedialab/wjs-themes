---
description: Django template formatting rules, sourced from this repo's djlint configuration
---

# Django Template Formatting (djlint)

The shared Django rules in
[`.claude/rules/code-style-django.md`](.claude/rules/code-style-django.md) apply too —
this file goes deeper on templates specifically, using this repo's djlint config
(`[tool.djlint]` in `pyproject.toml`) as the source of truth.

## Configuration

```toml
[tool.djlint]
profile="django"
ignore="H006"
```

- `profile="django"` scopes the active rule set to Django's template language: codes
  that only apply to Jinja (`J*`), Nunjucks, or Handlebars/meta-linting (`N*`, `M*`)
  are dropped. What's left is `H*` (generic HTML), `T*` (template-tag syntax), and
  `D*` (Django-specific) codes.
- `ignore="H006"` disables "Img tag should have height and width attributes" —
  `<img>` tags in this repo are not required to declare explicit dimensions.
- Nothing else is set, so every other djlint default applies as-is: 4-space
  `indent`, `max_line_length` 120, `max_attribute_length` 70, no
  `blank_line_before_tag`/`blank_line_after_tag`, `format_css`/`format_js` off.

**Known inconsistency:** existing templates in this repo are hand-formatted with
**2-space** indentation (e.g.
`wjs/themes/wjs-bootstrap/templates/wjs/base/elements/footer.html`, and see
`.editorconfig`'s `[*.html]` section), which contradicts djlint's un-overridden
4-space default. This still isn't caught by djlint itself: `.pre-commit-config.yaml`
only wires up the `djlint-django` hook (`djlint --profile=django`, lint-only) — the
reformatter (`djlint --reformat`) is never run automatically, so indentation is a
manual convention as far as djlint is concerned. Match the 2-space convention of the
surrounding file by hand; don't assume a passing pre-commit run says anything about
indentation, and don't run `djlint --reformat` without `--indent 2` and a careful
diff review.

Indentation deliberately stays hand-reviewed rather than tool-enforced — both
options that were tried against this repo's real templates misfire:

- A generic "indent must be a multiple of 2" check (the `editorconfig-checker`
  hook's `Indentation`/`IndentSize` rules) flags ~20% of templates, but almost all
  of those are a legitimate, intentional style — wrapped tag attributes aligned
  under the first attribute, not a fixed 2-space step, e.g.:
  ```html
  <a class="wjs-showcase__article-sidebar-download ..."
     href="{% url 'article_download_galley' article.id galley.id %}">
  ```
  A line-based checker can't tell that apart from a real mistake, so
  `Indentation`/`IndentSize` are explicitly disabled in `.editorconfig-checker.json`.
- djlint's own `--reformat --indent 2` understands tag structure but isn't safe to
  run as an auto-fixer here either: on at least one real template it lost track of
  block nesting when an `{% if %}`/`{% endif %}` pair lived inside an HTML comment,
  and re-indented `{% endfor %}`/`</ul>`/`<li>` to the wrong level.

`max_line_length` is disabled for the same reason: a few templates embed long
single-line inline SVG defs via `{% with %}` (up to ~690 characters), which will
always exceed any sane ceiling and aren't a formatting mistake.

## Rules the `django` profile enforces (pre-commit-checked)

- **Template-tag syntax (`T*`)** — T001 wrap `{{ var }}` / `{% tag %}` in whitespace
  (`{{ var }}`, never `{{var}}`); T002 double-quote string args inside tags
  (`{% trans "..." %}`, never `'...'`); T003 name every `{% endblock %}`
  (`{% endblock content %}`); T027 no unclosed quotes inside tag syntax; T032 no
  doubled-up internal whitespace inside a tag; T034 no `{% ... }%` typos (missing
  the closing `%`).
- **Django-specific (`D*`)** — D004 use `{% static "path/to/file" %}` instead of a
  hardcoded `/static/...` URL; D018 use `{% url "name" %}` instead of a hardcoded
  internal path in `href`/`action`/`src`.
- **Generic HTML (`H*`)** — lowercase tag and attribute names (H009/H010);
  double-quoted attribute values with no stray spaces around `=` (H008/H011/H012);
  no duplicate attributes on one tag (H037); `<img>` needs `alt` (H013 — the
  companion `height`/`width` check, H006, is the one this repo disables);
  `<html>` needs `lang` (H005) and the document needs a `<title>` (H016); avoid
  inline `style=` (H021); avoid plain-HTTP links (H022); no raw entity references
  beyond the common ones (`&lt;`, `&gt;`, `&amp;`, `&quot;`, `&nbsp;`, ...) (H023);
  no more than the configured blank-line run (H014, `max_blank_lines` defaults to 0
  — i.e. no blank lines at all are allowed by default); a line break after
  `<h1>`–`<h6>` (H015); no `type=` attribute on `<script>`/`<style>` (H024); no
  empty tag pairs or empty `class`/`id` attributes (H020/H026); lowercase form
  `method` values (H029); a `<meta name="description">`/`keywords` tag is suggested,
  not required (H030/H031).
- **Shipped but inert for this profile** — H017 (self-close void tags), H035
  (self-close `<meta>`), and H036 (avoid `<br>`) all default to `off`
  (`default: false` in djlint) and this repo doesn't opt them back in via
  `include`; T028 (suggest spaceless tags, `{%- if -%}`) explicitly excludes the
  `django` profile in djlint itself, since that's a Jinja-only feature.

## Enforcement beyond djlint (.editorconfig)

`.editorconfig`'s `[*.html]` section is the source of truth for indentation and
line-length *style* (`indent_size = 2`, `max_line_length = 240`), but as noted
above nothing mechanically checks templates against it — those two checks are
explicitly turned off. What *is* mechanically enforced, via the
`editorconfig-checker` pre-commit hook (config in `.editorconfig-checker.json`,
scoped to `*.html`, same test-file exclusion as `djlint-django`): trailing
whitespace, final newline, line-ending style, and charset. These have no known
false positives against this repo's templates — treat a failure here as a real
mistake, not a style choice, unlike the disabled checks.

## Running it

```bash
djlint --profile=django wjs/                        # lint only — matches what pre-commit/CI run
pre-commit run djlint-django --all-files             # the actual hook, same as CI

pre-commit run editorconfig-checker --all-files      # trailing whitespace / final newline / EOL / charset

# reformatting is NOT run by pre-commit — use deliberately, review the diff, and
# pass --indent 2 to match the repo's existing convention rather than djlint's default of 4:
djlint --reformat --profile=django --indent 2 wjs/path/to/template.html
```

## Conventions this repo follows but djlint doesn't check

These aren't djlint rules — they're project convention, so nothing flags a
violation automatically:

- Application templates live under `templates/<app_name>/` — never in the global
  template namespace. **One deliberate exception in this repo:**
  `wjs/themes/apps.py::WJSThemesConfig.ready()` appends wjs-bootstrap's `templates/`
  dir to Django's global `TEMPLATES[0]["DIRS"]`, so it's reachable even when a
  journal has a different theme selected (see `.claude/rules/architecture-django.md`)
  — don't "fix" that by moving it under a namespaced path, it's intentional.
- No blank lines between `{% extends %}` / `{% load %}` tags; one blank line before
  the first `{% block %}`.
- 2-space indentation for HTML, with template tags indented as if they were HTML
  elements (see the "Known inconsistency" note above for why djlint won't enforce
  this for you).
