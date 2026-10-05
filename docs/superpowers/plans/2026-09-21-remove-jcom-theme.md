# Remove JCOM-theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the legacy `JCOM-theme` Janeway theme from `wjs-themes`, after migrating its one
still-live dependency (the newsletter email CSS) into `wjs-bootstrap`, and clean up the dead
references it leaves in `wjs-profile-project` and `wjs-submission-project`.

**Architecture:** Three independent git repos, each already checked out on branch
`feature/issue-2808-remove-jcom-theme`. Work proceeds repo by repo: `wjs-themes` first (it produces
the new stylesheets and removes the theme), then `wjs-profile-project` (points its template at the
new stylesheets, fixes its test fixtures, cleans dead references), then `wjs-submission-project`
(drops one dead setting). No repo's tasks block another's — they can be done in any order — but this
order matches the dependency direction described in the spec.

**Tech Stack:** Django/Janeway theme packages (SCSS via `libsass`, compiled by each theme's
`build_assets.py`), pytest for `wjs-profile-project`'s test suite. `wjs-themes` itself has no
automated test suite — verification there is manual, inside the local Janeway checkout at
`/home/yakky/Projects/projects/sissa-1.8/janeway/src`, which already has all three packages
installed editable.

**Spec:** `/home/yakky/Projects/projects/sissa-1.8/wjs-themes/docs/superpowers/specs/2026-09-21-remove-jcom-theme-design.md`

## Global Constraints

- No visible change to rendered newsletter emails — every color value carried over from
  JCOM-theme's newsletter CSS must be preserved exactly (see the color table in the spec).
- `wjs-bootstrap` must not gain a dependency on Materialize or on JCOM-theme's `color()`/map
  system — the replacement values are plain SCSS variables.
- Each `THEME_CSS_FILES` entry in a `build_assets.py` is compiled independently (its own
  `sass.compile()` call) — variables are **not** shared across entries; anything a new entry point
  needs must be defined in that entry point itself.
- Double quotes, 4-space indent, no single-quote strings — per each repo's
  `.claude/rules/code-style-python.md` — applies to the one Python edit in this plan
  (`wjs/themes/apps.py`).
- No bare `assert` without a message in new pytest code (`wjs-profile-project`'s
  `.claude/rules/tests.md` convention).
- Conventional Commits format for every commit message in every repo.

---

## Task 1: Migrate the newsletter SCSS into wjs-bootstrap

**Repo:** `wjs-themes`

**Files:**
- Create: `wjs/themes/wjs-bootstrap/assets/sass/_newsletter_body.scss`
- Create: `wjs/themes/wjs-bootstrap/assets/sass/_newsletter_mquery.scss`
- Create: `wjs/themes/wjs-bootstrap/assets/sass/newsletter_jcom.scss`
- Create: `wjs/themes/wjs-bootstrap/assets/sass/newsletter_jcomal.scss`
- Create: `wjs/themes/wjs-bootstrap/assets/sass/newsletter_mobile.scss`
- Modify: `wjs/themes/wjs-bootstrap/build_assets.py`

**Interfaces:**
- Produces: three new compiled static files reachable as `wjs-bootstrap/css/newsletter_jcom.css`,
  `wjs-bootstrap/css/newsletter_jcomal.css`, `wjs-bootstrap/css/newsletter_mobile.css` once
  `build_assets` runs. Task 4 (`wjs-profile-project`) points its template at these exact paths.
- Consumes: nothing from another task.

- [ ] **Step 1: Create `_newsletter_body.scss`**

This is the original `wjs-themes/wjs/themes/JCOM-theme/assets/sass/_newsletter_body.scss`, with
every Materialize `color($map, $key)` lookup replaced by a plain variable. `$primary` and
`$journal-color-darken-2` are expected to already be set by whichever entry point imports this
partial (see Step 3) — this file does not define them itself. `$newsletter-bg`/`$newsletter-border`
are journal-independent, so they're defined once, right here:

```scss
@import url("https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,300;0,400;0,700;1,300;1,400&display=swap");

$newsletter-bg: #fafafa;
$newsletter-border: #bdbdbd;

a {
  text-decoration: none;
  color: $journal-color-darken-2;
}

body {
  background: $newsletter-bg;
  font-family: "Roboto", sans-serif;
  padding: 1rem;
  text-align: left;
}

.container {
  clear: both;
  margin-bottom: 2.5rem;
  padding: 0;
  text-align: left;
}

.logos {
  background: none;
  margin-bottom: 1.25rem;

  &__left {
    float: left;
    max-width: 225px;
    margin-bottom: -1rem;

    img {
      width: 100%;
    }
  }

  &__line-text {
    font-size: 1.5rem;
    font-weight: bold;
    color: $primary;
    float: left;
    width: 75%;
    text-align: left;
    border-bottom: 4px solid $primary;
    margin-left: 20px;
    padding-top: 20px;
  }

  &__line {
    border-bottom: 1px solid $primary;
  }

  &__right {
    position: absolute;
    text-align: right;
    right: 20px;

    img {
      height: auto;
      width: 40px;
    }
  }
}

h2 {
  background: $newsletter-bg;
  color: $primary;
  border-bottom: 1px solid $primary;
  margin-top: 2rem;
  padding-bottom: 1rem;
}

.section-name {
  font-size: 0.75rem;
  font-weight: bold;
  text-transform: uppercase;
  margin-bottom: 0;
}

.title {
  color: $journal-color-darken-2;
  font-size: 1.5rem;
  margin-top: 0.5rem;
  margin-bottom: 0;
}

.author {
  font-size: 0.8rem;
  font-style: italic;
  margin-top: 0.5rem;
}

.date {
  color: $primary;
  margin-bottom: 0;
  margin-top: 1rem;
}

.divider {
  margin: 1.25rem 0;
}

.unsubscribe {
  font-size: 0.75rem;
  text-align: center;
}

.header {
  &-cell {
    &--right {
      text-align: right;
    }

    &--left {
      text-align: left;
    }
  }
}

.mobile-hidden {
  display: none;
}

.article {
  border-bottom: 1px solid $newsletter-border;
  width: 100%;
}
```

- [ ] **Step 2: Create `_newsletter_mquery.scss`**

Pure layout, no color lookups — copy verbatim from
`wjs/themes/JCOM-theme/assets/sass/_newsletter_mquery.scss`:

```scss
body {
  @media (min-width: 768px) {
    padding: 2rem !important;
  }
  @media (min-width: 1024px) {
    padding: 3rem !important;
  }
}

.container {
  @media (min-width: 768px) {
    padding: 0 2rem !important;
  }
}

.logos__left {
  @media (min-width: 768px) {
    max-width: 225px !important;
    align-content: start;
    display: flex;
    float: none;
    justify-content: flex-start;
  }
}

.logos__right {
  @media (min-width: 640px) {
    right: 55px !important;
  }

  @media (min-width: 768px) {
    max-width: 40px !important;
  }
}

.logos__line-text {
  @media (min-width: 520px) {
    padding: 40px 0 10px 0 !important;
    width: 45% !important;
  }

  @media (min-width: 640px) {
    width: 50% !important;
  }

  @media (min-width: 640px) {
    width: 55% !important;
  }

  @media (min-width: 768px) {
    width: 60% !important;
    font-size: 2rem !important;
    padding: 30px 0 10px 0 !important;
  }

  @media (min-width: 1024px) {
    width: 65% !important;
  }

  @media (min-width: 1280px) {
    width: 70% !important;
  }

  @media (min-width: 1440px) {
    width: 75% !important;
  }
}

.mobile-visible {
  @media (min-width: 1024px) {
    display: none !important;
  }
  @media (max-width: 1024px) {
    display: flex;
    align-items: flex-start;
  }
}

.mobile-hidden {
  @media (min-width: 1024px) {
    display: flex !important;
    align-items: flex-start;
  }
  @media (max-width: 1024px) {
    display: none;
  }
}

.article-info {
  @media (min-width: 1024px) {
    width: 85%;
  }
  @media (max-width: 1024px) {
    width: 100%;
  }
}

.article-date {
  @media (min-width: 1024px) {
    text-align: right;
    width: 15%;
  }
  @media (max-width: 1024px) {
    text-align: left;
    width: 100%;
  }
}
```

- [ ] **Step 3: Create the two per-journal entry points**

`newsletter_jcom.scss` — `$primary` is JCOM's brand color (matches `wjs_jcom.scss`'s own
`$primary`), `$journal-color-darken-2` is the exact hex JCOM-theme used for title/date/link text:

```scss
@charset "UTF-8";

$primary: #623d91;
$journal-color-darken-2: #4b2e72;

@import "newsletter_body";
```

`newsletter_jcomal.scss` — same pattern, JCOMAL's colors:

```scss
@charset "UTF-8";

$primary: #c00074;
$journal-color-darken-2: #910055;

@import "newsletter_body";
```

- [ ] **Step 4: Create `newsletter_mobile.scss`**

Copy verbatim from `wjs/themes/JCOM-theme/assets/sass/newsletter_mobile.scss` (including its
existing comment typo — not this plan's concern to fix):

```scss
@charset "UTF-8";

/* Mobile only stiles in a separate file because we must load it with data-premailer="ignore" tag */

@import "newsletter_mquery";
```

- [ ] **Step 5: Wire the three new stylesheets into `build_assets.py`**

Modify `wjs/themes/wjs-bootstrap/build_assets.py`. Find:

```python
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
```

Replace with:

```python
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
    BASE_THEME_DIR / "css" / "newsletter_jcom.css",
    BASE_THEME_DIR / "css" / "newsletter_jcomal.css",
    BASE_THEME_DIR / "css" / "newsletter_mobile.css",
]
```

- [ ] **Step 6: Verify by actually building the assets**

There's no automated test suite in this repo — verification is running the real build inside the
local Janeway checkout, which already has `wjs-themes` installed editable:

```bash
cd /home/yakky/Projects/projects/sissa-1.8/janeway/src
python manage.py build_assets
```

Expected: no `sass` compile errors; console shows `THEMES SCSS START` ... `THEMES collectstatic
DONE` (and, since JCOM-theme hasn't been deleted yet — that's Task 2 — also its own
`JCOM SCSS START` ... `JCOM collectstatic DONE`).

Then check the compiled output has the exact colors, byte for byte:

```bash
grep -c '#623d91\|#4b2e72' static/wjs-bootstrap/css/newsletter_jcom.css
grep -c '#c00074\|#910055' static/wjs-bootstrap/css/newsletter_jcomal.css
grep -c 'fafafa\|bdbdbd' static/wjs-bootstrap/css/newsletter_jcom.css
```

Expected: each `grep -c` prints a count > 0 (no `0` output, no missing-file error).

- [ ] **Step 7: Commit**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/wjs-themes
git add wjs/themes/wjs-bootstrap/assets/sass/_newsletter_body.scss \
        wjs/themes/wjs-bootstrap/assets/sass/_newsletter_mquery.scss \
        wjs/themes/wjs-bootstrap/assets/sass/newsletter_jcom.scss \
        wjs/themes/wjs-bootstrap/assets/sass/newsletter_jcomal.scss \
        wjs/themes/wjs-bootstrap/assets/sass/newsletter_mobile.scss \
        wjs/themes/wjs-bootstrap/build_assets.py
git commit -m "$(cat <<'EOF'
feat(themes): migrate newsletter CSS from JCOM-theme into wjs-bootstrap

Replaces Materialize's color()/map lookups with $primary (already defined
per journal in wjs-bootstrap) plus two new plain variables carrying the
exact same hex values JCOM-theme used, so rendered output is unchanged.

Issue: wjs/specs#2808

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Deregister and delete JCOM-theme

**Repo:** `wjs-themes`

**Files:**
- Modify: `wjs/themes/apps.py:16-19`
- Delete: `wjs/themes/JCOM-theme/` (entire directory)

**Interfaces:**
- Consumes: nothing new (Task 1 doesn't need to be merged first — the two changes are
  independent — but running Task 1 first means `build_assets` in this task's verification only
  ever sees the new, already-migrated newsletter stylesheets).
- Produces: `WJSThemesConfig.themes == ("wjs-bootstrap",)` — nothing downstream in this plan reads
  this directly, but it's what `install_themes` (Janeway management command) iterates.

- [ ] **Step 1: Drop `JCOM-theme` from the theme registry**

Modify `wjs/themes/apps.py`. Find:

```python
    themes = (
        "wjs-bootstrap",
        "JCOM-theme",
    )
```

Replace with:

```python
    themes = ("wjs-bootstrap",)
```

- [ ] **Step 2: Delete the JCOM-theme directory**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/wjs-themes
git rm -r wjs/themes/JCOM-theme
```

- [ ] **Step 3: Verify `install_themes` no longer touches JCOM-theme**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/janeway/src
python manage.py install_themes
```

Expected: no errors; output only mentions `wjs-bootstrap` (re-running against an existing correct
symlink is a documented no-op).

- [ ] **Step 4: Remove the now-dangling JCOM-theme symlink**

`install_themes` only manages themes still in the registry, so the old symlink into the deleted
directory is left behind as a dangling link — clean it up by hand (this touches only the local
Janeway checkout, not a git repo):

```bash
rm -f /home/yakky/Projects/projects/sissa-1.8/janeway/src/themes/JCOM-theme
ls /home/yakky/Projects/projects/sissa-1.8/janeway/src/themes/
```

Expected: the listing no longer includes `JCOM-theme`; `wjs-bootstrap` is still there (as a
symlink) alongside Janeway's own `material`/`OLH`/`clean` themes.

- [ ] **Step 5: Commit**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/wjs-themes
git add wjs/themes/apps.py
git commit -m "$(cat <<'EOF'
feat(themes): remove the legacy JCOM-theme

No journal currently selects it (verified against the journal_theme
setting in a dev database snapshot); its one live dependency, the
newsletter email CSS, was migrated into wjs-bootstrap in the previous
commit.

Issue: wjs/specs#2808

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

(The directory deletion from Step 2 is already staged by `git rm`, so it's included in the same
commit — `git status` should show no remaining changes after this commit.)

---

## Task 3: Update wjs-themes documentation

**Repo:** `wjs-themes`

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.claude/rules/architecture-django.md`
- Modify: `.claude/rules/tests.md`

**Interfaces:** none — documentation only, no code dependency on other tasks.

- [ ] **Step 1: Update `CLAUDE.md`**

Find:

```markdown
It provides two themes plus an "advanced admin" Django app:

- **wjs-bootstrap** (`wjs/themes/wjs-bootstrap/`): the actively developed Bootstrap 5-based theme, used
  both as a Janeway "Journal Theme" and as a plain Django template base for wjs-specific apps (e.g.
  wjs-review). Its templates are injected into Django's global `TEMPLATES[0]["DIRS"]` (see
  `wjs/themes/apps.py::WJSThemesConfig.ready()`), so wjs-bootstrap templates are always available
  regardless of which theme a journal has selected.
- **JCOM-theme** (`wjs/themes/JCOM-theme/`): legacy "Vetrinetta" theme derived from Janeway's `material`
  theme. Only used by journals that explicitly select it; not being actively developed.
- **advanced_admin** (`wjs/advanced_admin/`): a separate Django admin site (`AdvancedAdminSite`) exposing
```

Replace with:

```markdown
It provides one theme plus an "advanced admin" Django app:

- **wjs-bootstrap** (`wjs/themes/wjs-bootstrap/`): the actively developed Bootstrap 5-based theme, used
  both as a Janeway "Journal Theme" and as a plain Django template base for wjs-specific apps (e.g.
  wjs-review). Its templates are injected into Django's global `TEMPLATES[0]["DIRS"]` (see
  `wjs/themes/apps.py::WJSThemesConfig.ready()`), so wjs-bootstrap templates are always available
  regardless of which theme a journal has selected.
- **advanced_admin** (`wjs/advanced_admin/`): a separate Django admin site (`AdvancedAdminSite`) exposing
```

Find:

```markdown
      templates/                # overrides of Janeway core/journal/cms/forms/hijack templates
    JCOM-theme/
      assets/, fonts/, build_assets.py, templates/   # legacy theme, same pattern as wjs-bootstrap
    locale/{en,es,pt}/LC_MESSAGES/django.po   # translations
```

Replace with:

```markdown
      templates/                # overrides of Janeway core/journal/cms/forms/hijack templates
    locale/{en,es,pt}/LC_MESSAGES/django.po   # translations
```

Find:

```markdown
`python manage.py install_themes` (Janeway management command provided by this package,
`wjs/themes/management/commands/install_themes.py`) symlinks each theme in `WJSThemesConfig.themes`
(`wjs-bootstrap`, `JCOM-theme`) from this package into Janeway's `themes/` directory, and applies the
```

Replace with:

```markdown
`python manage.py install_themes` (Janeway management command provided by this package,
`wjs/themes/management/commands/install_themes.py`) symlinks each theme in `WJSThemesConfig.themes`
(`wjs-bootstrap`) from this package into Janeway's `themes/` directory, and applies the
```

- [ ] **Step 2: Update `.claude/rules/architecture-django.md`**

Find:

```markdown
- **`wjs/themes/apps.py::WJSThemesConfig`** — declares the theme names (`themes = ("wjs-bootstrap",
  "JCOM-theme")`) and, in `ready()`, appends `wjs-bootstrap/templates` to Django's global
```

Replace with:

```markdown
- **`wjs/themes/apps.py::WJSThemesConfig`** — declares the theme names (`themes = ("wjs-bootstrap",)`)
  and, in `ready()`, appends `wjs-bootstrap/templates` to Django's global
```

Find:

```markdown
- **`wjs/themes/wjs-bootstrap/build_assets.py` / `wjs/themes/JCOM-theme/build_assets.py`** — each
  theme's asset pipeline, matching Janeway's `manage.py build_assets` contract (a module-level
```

Replace with:

```markdown
- **`wjs/themes/wjs-bootstrap/build_assets.py`** — the theme's asset pipeline, matching Janeway's
  `manage.py build_assets` contract (a module-level
```

- [ ] **Step 3: Update `.claude/rules/tests.md`**

Find:

```markdown
2. From `janeway/src`, run `python manage.py install_themes` (provided by
   `wjs/themes/management/commands/install_themes.py`) to symlink `wjs-bootstrap`/`JCOM-theme`
   into Janeway's `themes/` directory and apply `wjs/install/settings.json`.
```

Replace with:

```markdown
2. From `janeway/src`, run `python manage.py install_themes` (provided by
   `wjs/themes/management/commands/install_themes.py`) to symlink `wjs-bootstrap`
   into Janeway's `themes/` directory and apply `wjs/install/settings.json`.
```

- [ ] **Step 4: Commit**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/wjs-themes
git add CLAUDE.md .claude/rules/architecture-django.md .claude/rules/tests.md
git commit -m "$(cat <<'EOF'
docs: stop describing JCOM-theme as a present theme

Issue: wjs/specs#2808

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Point wjs-profile-project's newsletter template and test fixtures at wjs-bootstrap

**Repo:** `wjs-profile-project`

**Files:**
- Modify: `wjs/jcom_profile/templates/wjs/newsletter/email/newsletter_template.html:10-11`
- Modify: `wjs/jcom_profile/tests/conftest.py:421` and `:743-744`
- Test: `wjs/jcom_profile/tests/test_newsletters.py` (new test, appended)

**Interfaces:**
- Consumes: the static paths `wjs-bootstrap/css/newsletter_jcom.css` /
  `wjs-bootstrap/css/newsletter_mobile.css` that Task 1 makes buildable (this task's test doesn't
  require the physical file to exist — `{% static %}` under the test settings' storage backend
  just builds the URL string — but production correctness depends on Task 1 having landed).
- Produces: nothing consumed elsewhere in this plan.

- [ ] **Step 1: Write the failing test**

Add to the end of `wjs/jcom_profile/tests/test_newsletters.py`:

```python
def test_newsletter_template_references_wjs_bootstrap_css(journal):
    """The newsletter email template must load its CSS from wjs-bootstrap, not JCOM-theme."""
    content = render_to_string(
        "wjs/newsletter/email/newsletter_template.html",
        {"journal": journal},
    )
    assert "wjs-bootstrap/css/newsletter_jcom.css" in content, "expected the per-journal newsletter stylesheet path"
    assert "wjs-bootstrap/css/newsletter_mobile.css" in content, "expected the mobile newsletter stylesheet path"
    assert "JCOM-theme" not in content, "JCOM-theme has been removed and must not be referenced"
```

Add the missing import. Find, in the same file's import block:

```python
from django.db.models import Q
from django.test import Client
```

Replace with:

```python
from django.db.models import Q
from django.template.loader import render_to_string
from django.test import Client
```

- [ ] **Step 2: Run it and confirm it fails**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/janeway/src
pytest ../../wjs-profile-project/wjs/jcom_profile/tests/test_newsletters.py::test_newsletter_template_references_wjs_bootstrap_css -v
```

Expected: FAIL — the first assertion fails because the template still emits `JCOM-theme/css/...`,
not `wjs-bootstrap/css/...`.

- [ ] **Step 3: Fix the template**

Modify `wjs/jcom_profile/templates/wjs/newsletter/email/newsletter_template.html`. Find:

```django
    <link rel="stylesheet" href="{% static "JCOM-theme/css/newsletter_" %}{{ journal.code|lower }}.css">
    <link rel="stylesheet" href="{% static "JCOM-theme/css/newsletter_mobile.css" %}" data-premailer="ignore">
```

Replace with:

```django
    <link rel="stylesheet" href="{% static "wjs-bootstrap/css/newsletter_" %}{{ journal.code|lower }}.css">
    <link rel="stylesheet" href="{% static "wjs-bootstrap/css/newsletter_mobile.css" %}" data-premailer="ignore">
```

- [ ] **Step 4: Run the test again and confirm it passes**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/janeway/src
pytest ../../wjs-profile-project/wjs/jcom_profile/tests/test_newsletters.py::test_newsletter_template_references_wjs_bootstrap_css -v
```

Expected: PASS.

- [ ] **Step 5: Update the test fixtures**

Modify `wjs/jcom_profile/tests/conftest.py`. Find:

```python
@pytest.fixture
def press(install_jcom_theme):
    """Prepare a press."""
    # Copied from journal.tests.test_models
    apress = Press.objects.create(domain="testserver", is_secure=False, name="Medialab")
    apress.theme = "JCOM-theme"
    apress.save()
    yield apress
```

Replace with:

```python
@pytest.fixture
def press(install_jcom_theme):
    """Prepare a press."""
    # Copied from journal.tests.test_models
    apress = Press.objects.create(domain="testserver", is_secure=False, name="Medialab")
    apress.theme = "wjs-bootstrap"
    apress.save()
    yield apress
```

Find:

```python
@pytest.fixture
def install_jcom_theme():
    """JCOM-theme must be installed in J. code base for its templates to be found."""
    management.call_command("install_themes")
```

Replace with:

```python
@pytest.fixture
def install_jcom_theme():
    """Themes must be installed in J. code base for their templates to be found."""
    management.call_command("install_themes")
```

(The fixture keeps its name — it's only used by the `press` fixture above, and renaming it isn't
part of this change's scope — just its docstring, which no longer names a theme that's about to be
deleted.)

- [ ] **Step 6: Run the affected test files**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/janeway/src
pytest --create-db ../../wjs-profile-project/wjs/jcom_profile/tests/test_newsletters.py -v
pytest ../../wjs-profile-project/wjs/jcom_profile/tests/test_views.py -v
```

Expected: all PASS (no test in either file asserts on the literal string `"JCOM-theme"`, and
nothing in these flows resolves `press.theme` into an actual template-directory lookup, so the
fixture change is a no-op for current behavior — this run is a regression check, not expected to
change any outcomes).

- [ ] **Step 7: Commit**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/wjs-profile-project
git add wjs/jcom_profile/templates/wjs/newsletter/email/newsletter_template.html \
        wjs/jcom_profile/tests/conftest.py \
        wjs/jcom_profile/tests/test_newsletters.py
git commit -m "$(cat <<'EOF'
fix(newsletter): point newsletter email CSS at wjs-bootstrap

JCOM-theme is being removed (wjs/wjs-themes); its newsletter stylesheets
were migrated to wjs-bootstrap with identical colors. Also stops the
press test fixture from selecting the soon-to-be-deleted theme.

Issue: wjs/specs#2808

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Clean up dead JCOM-theme references in wjs-profile-project

**Repo:** `wjs-profile-project`

**Files:**
- Delete: `build_assets.sh`
- Modify: `.prettierignore:1`
- Modify: `setup-docs/ansible/wjs-test__create-instance__wjs.yml:246`
- Modify: `CLAUDE.md:18-19`, `CLAUDE.md:52`

**Interfaces:** none — cleanup only, no code depends on these.

- [ ] **Step 1: Delete `build_assets.sh`**

It already points at a path that has never existed in this repo
(`wjs-profile-project/wjs/themes/JCOM-theme/assets` — themes live in the `wjs-themes` repo, not
here):

```bash
cd /home/yakky/Projects/projects/sissa-1.8/wjs-profile-project
git rm build_assets.sh
```

- [ ] **Step 2: Drop the matching `.prettierignore` entry**

Modify `.prettierignore`. Find:

```
wjs/themes/JCOM-theme/assets/materialize-src/**
wjs/plugins/wjs_review/static/css/datatables.css
```

Replace with:

```
wjs/plugins/wjs_review/static/css/datatables.css
```

- [ ] **Step 3: Drop the ansible `rm -f themes/JCOM-theme` step**

Modify `setup-docs/ansible/wjs-test__create-instance__wjs.yml`. Find:

```yaml
        - "{{ python }} -mmanage link_plugins"
        - "{{ python }} -mmanage install_plugins"
        - rm -f themes/JCOM-theme
        - "{{ python }} -mmanage install_themes"
```

Replace with:

```yaml
        - "{{ python }} -mmanage link_plugins"
        - "{{ python }} -mmanage install_plugins"
        - "{{ python }} -mmanage install_themes"
```

- [ ] **Step 4: Update `CLAUDE.md`**

Find, inside the `### Setup` fenced bash block, this one line:

```
./build_assets.sh                         # compile JCOM-theme frontend assets (needs inotify-tools)
```

Delete it, so the block becomes just:

```bash
pip install -e .[test]                    # install into Janeway's virtualenv, from this repo's dir
python manage.py run_customizations       # from janeway/src: apply all WJS customizations to Janeway
```

Find:

```markdown
- `wjs.jcom_profile.apps.JCOMProfileConfig.ready()` monkeypatches `core.forms.RegistrationForm`, inserts this app's `templates/` dir at the front of Janeway's template `DIRS` (so WJS templates can override JCOM-theme/Janeway templates), and registers hook functions (`extra_corefields`, `extra_article_metadata`, `extra_edit_profile_parameters`, `extra_edit_subscription`) into Janeway's `core.plugin_loader`.
```

Replace with:

```markdown
- `wjs.jcom_profile.apps.JCOMProfileConfig.ready()` monkeypatches `core.forms.RegistrationForm`, inserts this app's `templates/` dir at the front of Janeway's template `DIRS` (so WJS templates can override Janeway templates), and registers hook functions (`extra_corefields`, `extra_article_metadata`, `extra_edit_profile_parameters`, `extra_edit_subscription`) into Janeway's `core.plugin_loader`.
```

- [ ] **Step 5: Confirm no reference is left**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/wjs-profile-project
grep -rn "JCOM-theme" --include="*.py" --include="*.html" --include="*.sh" --include="*.yml" --include="*.md" --include="*.prettierignore" . 2>/dev/null | grep -v "\.worktrees/"
```

Expected: no output (the remaining hits from the original investigation — stale `.po`
source-location comments and the already-dead `_obsolete_check_jcom_settings.py` — are explicitly
out of scope per the spec, and neither matches the file extensions checked here anyway except the
`.po` files, which this grep also excludes on purpose).

- [ ] **Step 6: Commit**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/wjs-profile-project
git add -u .prettierignore \
        setup-docs/ansible/wjs-test__create-instance__wjs.yml CLAUDE.md
# build_assets.sh's deletion was already staged by `git rm` in Step 1.
git commit -m "$(cat <<'EOF'
chore: drop dead JCOM-theme references

build_assets.sh pointed at a path that never existed in this repo; the
ansible rm step and .prettierignore entry were leftovers for a theme
that's being removed from wjs-themes.

Issue: wjs/specs#2808

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Drop the dead BOOTSTRAP5 setting in wjs-submission-project

**Repo:** `wjs-submission-project`

**Files:**
- Modify: `wjs/defaults/settings_submission.py:132-138`

**Interfaces:** none — this setting is confirmed dead (never imported into any active settings
module; only `INSTALLED_APPS`/`SUBMISSION_ARTICLE_LANGUAGES` are cherry-picked from this module
elsewhere).

- [ ] **Step 1: Remove the setting and its comment**

Modify `wjs/defaults/settings_submission.py`. Find:

```python
YAKUNIN_URL = "http://janeway-services.ud.sissamedialab.it:1235/watermark/"


# Override the default bootstrap5 css as we customize it, and the css below will include all the bootstrap5 css plus
# our own customizations
# We might have an issue if we want to customize this per journal, but I would leave as an issue as it has a low impact
# for now as it's just the dashboard css
BOOTSTRAP5 = {"css_url": "/static/JCOM-theme/css/wjs_review.css"}


SUBMISSION_ARTICLE_LANGUAGES = {
```

Replace with:

```python
YAKUNIN_URL = "http://janeway-services.ud.sissamedialab.it:1235/watermark/"


SUBMISSION_ARTICLE_LANGUAGES = {
```

- [ ] **Step 2: Confirm nothing references it**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/wjs-submission-project
grep -rn "BOOTSTRAP5" --include="*.py" .
```

Expected: no output.

- [ ] **Step 3: Sanity-check the module still imports cleanly**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/wjs-submission-project
python -m py_compile wjs/defaults/settings_submission.py
```

Expected: no output, exit code 0.

- [ ] **Step 4: Commit**

```bash
cd /home/yakky/Projects/projects/sissa-1.8/wjs-submission-project
git add wjs/defaults/settings_submission.py
git commit -m "$(cat <<'EOF'
chore: drop dead BOOTSTRAP5 setting referencing JCOM-theme

Never imported into any active settings module (only INSTALLED_APPS and
SUBMISSION_ARTICLE_LANGUAGES are cherry-picked from settings_submission.py
elsewhere) — dead code referencing a theme that's being removed.

Issue: wjs/specs#2808

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```
