# Evaluation — shared-article-admin-search-filters

- **Date:** 2026-11-10
- **Branch:** feature/issue-3329-shared-article-admin-filters in wjs-themes, wjs-submission-project, wjs-profile-project (working tree vs origin/wjs-develop)
- **Task:** wjs/specs#3329
- **Coverage:** full (all touched Python files in the three repos; templates untouched)

## Scores
| Dimension | Score | Weight | Key evidence |
|---|---|---|---|
| Functionality | 4 | 20 | Spec goals 1–4 met: shared search/filters on 3 pages (`wjs-themes/wjs/advanced_admin/admin.py` `ArticleSearchFilterMixin`), unaccent, state-editable page; JQuant_4050 found by 7 terms on all 3 admins on local DB; final review's admin.E040 regression fixed; email/identifier also get the unaccented term (spec: plain) |
| Testing | 4 | 15 | RED→GREEN per task; `test_admin_article_search.py` covers the 5 Review Focus inputs + E040 check; suite 387 passed + 1 known local failure; Article page tested only via get_search_results/ChangeList, accents only on synthetic data (local DB has none) |
| Security | 4 | 15 | `unaccent_term` uses a parameterized query (`cursor.execute("SELECT unaccent(%s)", [term])`); page superuser-only (local DB: no non-superuser staff); raw state edit is the agreed option A with on-page warning |
| Code quality | 4 | 15 | One regex (`ARTICLE_PK_RE`) and one mixin replace two ad hoc overrides (`advanced_admin.py` −26 lines); pre-commit clean in 3 repos; `search_fields` set in `__init__` is a slightly unusual but documented shape |
| Maintainability | 3 | 15 | Pages differ only by `article_lookup_prefix` / `workflow_state_lookup`; but wjs-themes search depends on an extension created by a wjs-submission migration and a test-only `django_db_setup` duplicated in two conftests |
| Error handling | 3 | 10 | Blank term short-circuits before any query; a DB without `unaccent` raises a raw ProgrammingError (500) on any search — guarded only by deploy order (migration 0025) |
| Documentation | 3 | 10 | Docstrings on mixin, helper, admin methods; spec/plan saved; wjs-themes CLAUDE.md still describes only `ArticleSearchMixin` (doc-sync pending); warning text says "no log entry" while Django's admin LogEntry is written |

## Recommendations
- Maintainability: note in the MR that wjs-submission (migration 0025) must be deployed with or before wjs-themes 2.1.11.
- Error handling: state the `unaccent` prerequisite in the MR "Required actions" (migrations; PostgreSQL ≥ 13 or superuser for `CREATE EXTENSION`).
- Documentation: update wjs-themes CLAUDE.md / wjs-profile docs for the new mixin and page; reword the warning to "no workflow log entry".

## Total
**73%** — Solid, well-tested feature; cross-package `unaccent` dependency and docs are the weak spots.
