# Remove JCOM-theme — Design

## Context

`wjs-themes` ships two Janeway themes: `wjs-bootstrap` (the current Bootstrap5-based theme, used
by all live journals) and `JCOM-theme` (the legacy Materialize-based "Vetrinetta" theme it
replaced). `JCOM-theme` is dead weight: it is no longer selected by any journal, but it is still
registered, still symlinked into every Janeway checkout via `install_themes`, and still has a few
lingering references elsewhere in the `wjs-*` repo family.

**Investigation findings** (repo greps + a direct read-only query against the local dev database,
`janeway_t5`):

- **Registration point:** `wjs/themes/apps.py`'s `WJSThemesConfig.themes = ("wjs-bootstrap",
  "JCOM-theme")` — this is what `install_themes` uses to symlink themes into Janeway's `themes/`
  dir.
- **Database:** in `janeway_t5`, the `journal_theme` setting for all 7 journals (JCOM, JCOMAL,
  JQuant, JCAP, JHEP, JSTAT, JINST) is `wjs-bootstrap` or `clean`; the press-level theme is `OLH`.
  No journal or press currently selects `JCOM-theme`. This is one dev/test snapshot, not
  production — worth a second check there before/at deploy time, but nothing in this spec depends
  on that check succeeding.
- **One live functional dependency:** `wjs-profile-project`'s newsletter email template
  (`wjs/jcom_profile/templates/wjs/newsletter/email/newsletter_template.html`) hardcodes
  `{% static "JCOM-theme/css/newsletter_<journalcode>.css" %}` and `newsletter_mobile.css`.
  `wjs-bootstrap` has no equivalent newsletter stylesheet today. This is the one piece of
  JCOM-theme that must be migrated, not just deleted.
- **One live test dependency:** `wjs-profile-project`'s `conftest.py` sets `apress.theme =
  "JCOM-theme"` on a press fixture, with an existing comment already noting the theme is "stale
  and on its way out."
- **Everything else found** (a dead `BOOTSTRAP5` setting in `wjs-submission-project`, a broken
  `build_assets.sh` path and a `.prettierignore` entry in `wjs-profile-project`, an `rm -f
  themes/JCOM-theme` line in an ansible playbook, stale `.po` source-location comments, `CLAUDE.md`
  mentions) is dead or cosmetic — no functional dependency, just cleanup.

## Goal

Remove `JCOM-theme` entirely from `wjs-themes`, with no visible change to rendered output anywhere
it's still actually used (the newsletter emails), and clean up the now-dead references it leaves
behind in the sibling repos that mention it.

## Approach: rewrite the newsletter CSS, don't copy it

The newsletter styles (`_newsletter_body.scss`, `_newsletter_mquery.scss`) only touch 4 color
values, resolved today via Materialize's `color($map, $key)` function:

| Lookup | Value | Used for |
|---|---|---|
| `color("journal-color", "base")` | `#623d91` (JCOM) / `#c00074` (JCOMAL) | links, header underline |
| `color("journal-color", "darken-2")` | `#4b2e72` (JCOM) / `#910055` (JCOMAL) | title/date text |
| `color("grey", "lighten-5")` | `#fafafa` | page/heading background |
| `color("grey", "lighten-1")` | `#bdbdbd` | article divider border |

`wjs-bootstrap`'s per-journal stylesheets (`wjs_jcom.scss`, `wjs_jcomal.scss`) already define
`$primary: #623d91` / `#c00074` — **identical** to the "journal-color base" values above. The
other three values have no existing equivalent in `wjs-bootstrap` (Bootstrap's own `$gray-*` ramp
uses different hex stops than Materialize's `grey` map, and there's no precomputed "darken-2"
variant of `$primary` anywhere).

Rather than copying Materialize's map/`color()` machinery (which would also drag in
`components/_color-variables.scss`) into `wjs-bootstrap`, or accepting a lossy rewrite via
Bootstrap's `shade-color()` function (which won't reproduce the exact existing hexes without
tuning), the plan is:

- Reuse `$primary` for the "base" lookup (exact match, already there).
- Replace the other 3 lookups with new plain SCSS variables hardcoded to their **existing exact
  hex values** — no color computation, no map, no `color()` calls.

Net effect: pixel-identical rendered output, no Materialize dependency, and the one lookup that
had a real equivalent (`$primary`) is reused instead of duplicated.

I also checked every CSS class used across all 4 newsletter templates (`newsletter_template.html`,
`newsletter_article.html`, `newsletter_issue.html`, `newsletter_news.html`) against Materialize's
utility/grid classes (`components/_color-classes.scss`, `components/_normalize.scss`) — none are
used. Confirms those two files were dead weight in JCOM-theme's own build too, not just for this
migration.

## Changes

### `wjs-themes`

1. **Rewrite `_newsletter_body.scss`** (moved to `wjs/themes/wjs-bootstrap/assets/sass/`):
   - Replace `color("journal-color", "base")` → `$primary`, `color("journal-color", "darken-2")`
     → `$journal-color-darken-2`, `color("grey", "lighten-5")` → `$newsletter-bg`,
     `color("grey", "lighten-1")` → `$newsletter-border`. These four variables are expected to
     already be in scope when this partial is `@import`-ed (see point 3) — `_newsletter_body.scss`
     itself defines none of them.
   - The journal-independent greys (`$newsletter-bg: #fafafa`, `$newsletter-border: #bdbdbd`) are
     defined once, directly in `_newsletter_body.scss` itself, above their first use — they don't
     vary per journal so there's no duplication concern for them.
   - Drop the `@import` block at the top of `newsletter_jcom.scss`/`newsletter_jcomal.scss`
     (Materialize color-variables, color-classes, variables, normalize, JCOM's own
     color-variables/variables) — no longer needed.
2. **Move `_newsletter_mquery.scss`** to `wjs-bootstrap/assets/sass/` as-is (pure layout, no color
   lookups — verified above).
3. **Move `newsletter_jcom.scss` and `newsletter_jcomal.scss`** to `wjs-bootstrap/assets/sass/`,
   trimmed to `$primary` + `$journal-color-darken-2` + `@import "newsletter_body"`. Each
   `THEME_CSS_FILES` entry in `build_assets.py` is compiled independently (its own `sass.compile()`
   call on that one file) — there is no shared compile pass with `wjs_jcom.scss`/`wjs_jcomal.scss`,
   so `$primary` is **not** inherited from them and must be set directly in these two files too.
   That duplicates one hex literal per journal across two files, which matches this codebase's
   existing convention (`wjs_jcom.scss`/`wjs_jcomal.scss` already hardcode their own hex literals
   independently rather than sharing a single source of truth) rather than introducing a new
   shared-partial abstraction for two call sites.
4. **Move `newsletter_mobile.scss`** to `wjs-bootstrap/assets/sass/` unchanged (just `@import
   "newsletter_mquery"`).
5. **Update `wjs-bootstrap/build_assets.py`**: add `newsletter_jcom.css`, `newsletter_jcomal.css`,
   `newsletter_mobile.css` to `THEME_CSS_FILES`.
6. **Update `wjs/themes/apps.py`**: drop `"JCOM-theme"` from `WJSThemesConfig.themes`.
7. **Delete `wjs/themes/JCOM-theme/` entirely** (templates, assets, `build_assets.py`, `__pycache__`).
8. **Update `CLAUDE.md`**: remove the "two themes" framing and JCOM-theme's description.

### `wjs-profile-project`

1. **`wjs/jcom_profile/templates/wjs/newsletter/email/newsletter_template.html`**: change both
   `{% static %}` paths from `JCOM-theme/css/...` to `wjs-bootstrap/css/...`.
2. **`wjs/jcom_profile/tests/conftest.py`**: change `apress.theme = "JCOM-theme"` to
   `"wjs-bootstrap"`; drop the comment about needing JCOM-theme installed for its templates to be
   found (no longer applicable).
3. **`build_assets.sh`**: fix or remove — it currently points at
   `wjs-profile-project/wjs/themes/JCOM-theme/assets`, a path that has never existed in this repo.
4. **`.prettierignore`**: drop the `wjs/themes/JCOM-theme/assets/materialize-src/**` entry (same
   nonexistent path).
5. **`setup-docs/ansible/wjs-test__create-instance__wjs.yml`**: drop the `rm -f
   themes/JCOM-theme` step (becomes a no-op once `wjs-themes` step 6 lands; harmless to leave, but
   dead).
6. **`CLAUDE.md`**: update the one mention of JCOM-theme/Janeway templates to stop implying
   JCOM-theme is present.

### `wjs-submission-project`

1. **`wjs/defaults/settings_submission.py`**: drop the dead `BOOTSTRAP5 = {"css_url":
   "/static/JCOM-theme/css/wjs_review.css"}` line — confirmed unused (never imported into any
   active settings module, only `INSTALLED_APPS`/`SUBMISSION_ARTICLE_LANGUAGES` are cherry-picked
   from this module elsewhere).

### Out of scope

- `wjs-profile-project/wjs/jcom_profile/management/commands/_obsolete_check_jcom_settings.py` —
  already-dead file, unrelated broader cleanup.
- Locale `.po` stale `#:` source-location comments pointing at deleted JCOM-theme template paths —
  self-heal on the next `makemessages` run, no action needed.
- Verifying the `journal_theme`/press `theme` settings against the production database — the dev
  snapshot check found nothing, but this spec doesn't block on a production check.

## Verification

- `wjs-themes`: run `build_assets` (or the theme's own `build_assets.py` directly) after the
  rewrite and diff the compiled `newsletter_jcom.css`/`newsletter_jcomal.css`/
  `newsletter_mobile.css` against the pre-change JCOM-theme output — should be byte-identical
  modulo selector/comment ordering, since every color value is preserved exactly.
- `wjs-profile-project`: render the newsletter template (existing newsletter tests, if any, or a
  manual `send_newsletter`/preview) against both JCOM and JCOMAL journals and confirm styling is
  unchanged.
- `wjs-profile-project`: run the test suite (`pytest --create-db -n7 ../../wjs-profile-project`
  from `janeway/src`) — the `conftest.py` fixture change should be transparent to existing tests.
- Confirm `install_themes` no longer symlinks `JCOM-theme` after the `apps.py` change, and that a
  fresh checkout has no dangling `themes/JCOM-theme` symlink.
