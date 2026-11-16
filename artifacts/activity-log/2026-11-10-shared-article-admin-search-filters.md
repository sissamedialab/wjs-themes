## 2026-11-10 — Shared search and filters for the advanced admin article pages
**What:** The Articles, Article submissions (wjs-submission) and new Article workflows (wjs-profile) pages of the advanced admin now share one search and filter set through `ArticleSearchFilterMixin`. Search ignores diacritics in titles and names. The new Article workflows page lets the EO set a paper's `state` directly.
**Why:** specs#3329. The tester found that a `JQuant_4365` label, a title word, the correspondence email and an accented surname ("Rudziński", typed with ń or n) found nothing on Articles, and that "Munizzi" and the correspondence email found nothing on Article submissions. The Article workflows page did not exist.
**Decisions:**
- **Raw state edit with a warning on the form (option A).** Chosen because `/admin/` already allows it: `FSMField` is not `protected`. It runs no transition, notification, workflow log or `latest_state_change` update. Add and delete are disabled.
- **Accent-insensitive search done in this issue.** It uses PostgreSQL `unaccent` on the title and the names. The extension is created by wjs-submission migration `0025_unaccent_extension`, so wjs-themes now depends on that migration at runtime.
- **The search term is normalised with `SELECT unaccent(%s)`.** So accented and plain spellings match in both directions.
- **pk and label search.** A bare pk or `<CODE>_<pk>` matches the exact pk, and that result is OR'ed with the normal text search. This means `JCOM_4515` also finds papers whose identifier contains it.
- **`search_fields` is set in the mixin's `__init__`, not in `get_search_fields`.** The admin.E040 check for `ArticleCollaborationInline.autocomplete_fields` reads the attribute. The first version broke `manage.py check`, which the final review caught.
- **EO access.** Checked on the local DB: 27 EO users, 20 superusers, 0 non-superuser staff. The EO group has 0 permissions, so in practice the page is used by superusers.
- **Execution rulings:**
  - No commits during implementation (working tree only).
  - `makemigrations --check` shows a `CollaborationProxy` drift that was already there.
  - Article workflows list shows `article` (its `__str__` is pk and title) plus journal and state.
  - An `-n4` duplicate-key failure came from stale worker DBs; it passes on a serial `--create-db` run.
**Agent usage:**

| Stage | Agent/skill | Tokens | Time |
|---|---|---|---|
| Design | superpowers:brainstorming (builder-check subagent) | ≈80k | ≈1m |
| Implementation | superpowers:executing-plans (inline, no subagent) | — | — |
| Review | superpowers:requesting-code-review (final reviewer, opus) | ≈91k | ≈3m |

**Considered & dropped:**
- **Option B, running real FSM transitions from the admin.** Too heavy for an admin page, and it is not what the issue asked for.
- **Leaving diacritics for a later issue.** Dropped because the tester's failing case depends on it.
- **Overriding `get_search_fields`.** Dropped because of E040.
**Follow-ups:**
- Deploy wjs-submission (migration 0025) with or before wjs-themes 2.1.11. A DB without `unaccent` returns a 500 on every search. `CREATE EXTENSION` needs PostgreSQL ≥ 13 or a superuser.
- Deferred minors:
  - Email and identifier fields also receive the unaccented term.
  - `unaccent_term` uses the default DB connection.
  - The warning says "no log entry", but Django's admin LogEntry is still written.
  - `ARTICLE_PK_RE` can over-match terms like `jcom_2023_02`. This behaviour already existed.
- Diacritic search is verified only by tests, because local names are anonymized. Check it on test-dev.
- Playwright was skipped by choice; the change is admin-only.
- Eval: 73% — artifacts/evaluations/2026-11-10-shared-article-admin-search-filters.md
**Refs:**
- https://gitlab.sissamedialab.it/wjs/specs/-/work_items/3329
- spec: artifacts/specs/2026-11-10-shared-article-admin-search-filters-design.md
- plan: artifacts/plans/2026-11-10-shared-article-admin-search-filters.md
- branch `feature/issue-3329-shared-article-admin-filters` in all three repos
