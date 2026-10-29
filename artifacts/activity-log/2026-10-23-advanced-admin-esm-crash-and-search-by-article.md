## 2026-10-23 — Advanced admin: ESM `__str__` crash and search by article
**What:** Fixed the ESM changelist crash (`__str__ returned non-string`) and made the advanced-admin
file pages (ESM, "Manuscript files, ESM and admin files", their autocompletes) searchable by article
identifier (`JCOM_4515` / `4515`) and title word; "Article submission" (wjs-submission-project) also
searches `article__title` now.
**Why:** Janeway's `SupplementaryFile.__str__` returns `file.label`, which is nullable; Django 5 calls
`str(obj)` for every changelist row (`action_checkbox` aria-label), so any page with a label-less ESM
500s — the search term only decides which rows are on the page. Staff also could not find a paper's
files: those admins only searched file metadata.
**Decisions:**
- `__str__` fixed on `SupplementaryFileProxy` only (label → `original_filename` fallback), no change
  to the Janeway fork — user's call. Known limit: the Article change page's `supplementary_files`
  widget/autocomplete still uses Janeway's base `__str__`.
- ESM admins search via the real reverse M2M `Article.supplementary_files` (`supp__title`,
  `supp__identifier__identifier`) in plain `search_fields`, so an ESM matches the article it is
  attached to.
- `File` has no relation to `Article` (`File.article_id` is a plain integer), so `FileAdmin` /
  `FileAutocompleteAdmin` use `ArticleSearchMixin`: `Article` id subquery by identifier/title, OR-ed
  with the stock search; `may_have_duplicates` left to `super()` (an `IN` subquery can't duplicate).
- wjs-themes has no test suite: verified with a throwaway pytest file run on wjs-submission's test
  infra (17/17, RED first); wjs-submission got committed tests. Eval: 75% —
  artifacts/evaluations/2026-10-23-advanced-admin-esm-search.md
**Agent usage:**

| Stage | Agent/skill | Tokens | Time |
|---|---|---|---|
| Review | general-purpose reviewer (opus) | ~68k | ~2m |

**Considered & dropped:** fixing `SupplementaryFile.__str__` in the Janeway fork (fork divergence);
mixin on the ESM admins via `file__article_id` (first version — replaced by declarative
`search_fields` where a relation exists); plain `search_fields` for `File` via the reverse M2Ms (~8
joins and still misses files linked only by `article_id`, e.g. galleys, cover letters).
**Follow-ups:** manual check on test-dev (JQuant ESM "supplementary"; JCOM `4515` / `Interpreting` on
ESM, Files, Article submission); deferred minors — quoted `"phrase"` not unquoted in the mixin,
numeric terms match any identifier type, mixin subquery is a seq scan; title search with a non-English
admin UI (modeltranslation) unverified.
**Refs:** wjs/specs#3198; spec `artifacts/specs/2026-10-23-advanced-admin-esm-search-design.md`; plan
`artifacts/plans/2026-10-23-advanced-admin-esm-search.md`; same-named branch in wjs-submission-project.
