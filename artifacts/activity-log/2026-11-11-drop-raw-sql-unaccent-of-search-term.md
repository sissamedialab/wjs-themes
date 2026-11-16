## 2026-11-11 — Dropped the raw SQL unaccent of the admin search term
**What:**
- Removed `unaccent_term` (`SELECT unaccent(%s)` on a raw cursor) from `wjs/advanced_admin/admin.py`.
  `ArticleSearchFilterMixin.get_search_results` now passes the term unchanged to the standard admin search.
- Added filter tests: wjs-submission `tests/test_admin_article_filters.py`, plus the workflow state filters in
  wjs-profile.
**Why:** Review on wjs-themes!157 (Iacopo) said raw SQL is not worth it for this and asked for an ORM way.
**Decisions:**
- **No replacement is needed.** Django's `Unaccent` transform is `bilateral = True`, so `field__unaccent__icontains`
  already wraps the term in `UNACCENT()`. Checked against the generated SQL. The accented/plain tests pass in both
  directions.
- **Two deferred minors from the previous entry are now resolved:**
  - email and identifier no longer receive an unaccented term;
  - the search no longer queries the default connection directly.
- **Filter tests apply each filter through the changelist.** Each test first asserts that its query parameters belong
  to one of the page's filters, because Django applies a lookup on a model field even when that field has no filter.
  Mutation-checked: removing the `stage` filter, or the workflow `state` lookup, makes the tests fail.
**Follow-ups:**
- The CI of wjs-submission!192 and wjs-profile!1626 fails. The likely cause is that `wjs-themes >= 2.1.11` is not
  published yet (latest tag v2.1.10). Not confirmed from the job logs.
**Refs:**
- https://gitlab.sissamedialab.it/wjs/wjs-themes/-/merge_requests/157#note_81764
- previous entry: `2026-11-10-shared-article-admin-search-filters.md`
