## 2026-10-23 — Advanced admin search: match article pk, revert ESM `supp` search
**What:** Follow-up to `2026-10-23-advanced-admin-esm-crash-and-search-by-article.md`. All advanced-admin
file pages (ESM included) now go through `ArticleSearchMixin`, which also matches the article pk
(`4050` or the wjs-review label `JQuant_4050`); Article submission (wjs-submission) matches the pk too.
**Why:** Local testing showed `JQuant_4050` found nothing. That label is not an `Identifier`: wjs-review
builds it as `f"{journal.code}_{article.pk}"` (`wjs_review/states.py`). Also, on the local DB 798 of 917
`SupplementaryFile` are not in any `Article.supplementary_files`, while 912 have `file.article_id` — so
the earlier `supp__…` ESM search missed most ESM.
**Decisions:**
- ESM admins back on the mixin with `article_id_lookup = "file__article_id"` (the previous entry's
  `supp` M2M decision is reversed).
- pk matched exactly for `<digits>` / `<word>_<digits>`; bare numbers still also do identifier
  substring search (broad, e.g. 153 files for `4050` locally) — user's choice over narrowing to
  `iendswith("_<n>")`.
- Article submission: `=article__id` + a small label-to-digits `get_search_results` instead of reusing
  the wjs-themes mixin, to avoid pinning `wjs-themes >= 2.1.9` and coupling the releases.
- Verified: wjs-themes scratch tests 15/15 (RED first), real local DB (`JQuant_4050` → the 2 ESM and 7
  files of article 4050); wjs-submission admin tests 28/28.
**Follow-ups:** the code-eval report was not re-run for this follow-up; manual check on test-dev.
**Refs:** wjs/specs#3198; MRs wjs-themes!152, wjs-submission-project!185; spec "Revision 2".
