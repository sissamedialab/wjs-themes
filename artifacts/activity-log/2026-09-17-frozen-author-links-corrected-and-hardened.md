## 2026-09-17 — Author links: right pk, no 500, no N+1

**What:** All seven author-name links across both themes now link on
`FrozenAuthor.author_id` under an `{% if %}` guard, rendering the name as plain text
when a frozen author has no account. Template-only change; the companion view fix is
`wjs-profile-project!1510`.

**Why:** Three different spellings had accumulated, with three different behaviours,
all verified by rendering before the change:

- `{% url 'articles_by_author' au.pk %}` (2 sites) passed the **FrozenAuthor** pk to a
  URL expecting an **Account** pk — a silent link to an unrelated account, or a 404.
  This was the reported defect, found while reviewing the view-side fix for specs#3048.
- Unguarded `{% url ... au.author.pk %}` (3 sites) raised `NoReverseMatch` → **HTTP
  500** whenever `author` was NULL. `FrozenAuthor.author` is
  `null=True, on_delete=SET_NULL`, and imported legacy articles routinely have no
  account, so this was a live crash path on public pages.
- `{% url ... as var %}` (2 sites) did not crash but emitted `<a href="">` — an anchor
  that re-navigates to the current page.

**Decisions:**
- Condition the anchor rather than adopt the `{% url ... as %}` form: the latter is
  the smaller change but leaves a dead link in the output.
- All seven sites, not just the two reported — leaving three behaviours for one
  concept across two themes is how this drifted in the first place.
- **`author_id`, not `author`.** See gotchas.
- No test harness (the repo has none) and no componentisation (the two themes have
  materially different markup). Both recorded as follow-ups.

**Agent usage:**

| Stage | Agent/skill | Tokens | Time |
|---|---|---|---|
| Review | superpowers:requesting-code-review (general-purpose subagent) | ~122k | ~7m |

Design, implementation and wrap-up ran inline in the main session.

**Considered & dropped:**
- *Guarding with `{% url ... as var %}`* — prevents the crash, keeps the dead anchor.
- *Wrapping the long lines* — impossible without changing output: a newline between
  `{% endif %}` and the following `{# djlint:off #}` separator region renders as a
  space before the comma.
- *Componentising into one `author_link.html` per theme* — right long-term, but a
  refactor with its own review surface; declined for a P1 fix.

**Gotchas worth keeping:**
- **`{% if au.author %}` is an N+1.** Django's `ForwardManyToOneDescriptor` issues a
  SELECT per frozen author on cache miss, and nothing prefetches
  `frozen_authors__author` on these pages. The first version of this fix introduced
  that at the two `article_documents.html` sites, which previously issued *no* query
  — roughly +120 queries on a collection of 30 children × 4 authors. Using the local
  column `author_id` costs zero queries and also removed the pre-existing N+1 at the
  other five sites. Caught in code review, not by me.
- Template `{% url %}` with an unresolvable argument does **not** fail soft: Django
  substitutes `string_if_invalid` (empty string) and `reverse()` then rejects it
  against an `<int:...>` converter. The `as var` form swallows this; the bare form
  does not.
- Verifying template behaviour here needs no repo test infrastructure: ~60 lines of
  `settings.configure()` + `Template().render()` against a one-line URLconf reproduces
  all three failure modes with no database and no Janeway import. That is what sized
  the test-harness follow-up as small rather than unbounded.
- `.editorconfig` declares `max_line_length = 240` for HTML but
  `.editorconfig-checker.json` sets `"Disable": {"MaxLineLength": true}` — the ceiling
  is documentation, not a gate. Five touched lines now exceed it, accepted knowingly.

**Follow-ups:**
- Minimal template-rendering test harness for this repo (small — see gotchas).
- Shared author-link component per theme, once a harness exists.
- `author_link.html` loads `i18n` but never uses it; its aria-labels ("Go to all
  articles by …", "Send an email to …") are hardcoded English in a repo shipping
  `en`/`es`/`pt`. Pre-existing.
- Manual check on a running environment against an imported article whose
  `FrozenAuthor.author` is NULL — the only validation step that exercises the real
  queryset and the real CSS. **Not yet done.**
- Orphan names lose one SCSS selector (`_wjs_showcase.scss:306-315`, `a` inside
  `&__article-genealogy-item`) and the `btn-link` styling in `author_link.html`.
  Cosmetic; worth a screenshot.

**Refs:** [specs#3048](https://gitlab.sissamedialab.it/wjs/specs/-/work_items/3048);
companion MR [wjs-profile-project!1510](https://gitlab.sissamedialab.it/wjs/wjs-profile-project/-/merge_requests/1510);
spec `docs/superpowers/specs/2026-09-17-frozen-author-links-design.md`;
plan `docs/superpowers/plans/2026-09-17-frozen-author-links.md`;
Eval: 73% — artifacts/evaluations/2026-09-17-frozen-author-links.md
