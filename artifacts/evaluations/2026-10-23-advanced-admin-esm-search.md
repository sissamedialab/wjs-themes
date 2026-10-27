# Evaluation — advanced-admin-esm-search

- **Date:** 2026-10-23
- **Branch:** bugfix/issue-3198-advanced-admin-search in wjs-themes + wjs-submission-project (working tree)
- **Task:** wjs/specs#3198
- **Coverage:** full — `wjs-themes/wjs/advanced_admin/admin.py`, `wjs-submission-project/.../advanced_admin.py`, `tests/test_admin_article_submission_search.py`

## Scores
| Dimension | Score | Weight | Key evidence |
|---|---|---|---|
| Functionality | 4 | 20 | Crash reproduced (`TypeError` in `action_checkbox`) then fixed; `4515`/`JCOM_4515`/`Interpreting` find the paper on ESM, Files, autocompletes, Article submission; known limit (Article change-page widget uses Janeway `__str__`) accepted in spec |
| Testing | 3 | 15 | RED→GREEN on 15 scratch + 2 committed tests; full wjs-submission suite 290 pass / 1 pre-existing local failure; wjs-themes tests are throwaway (no suite) so no lasting regression guard there |
| Security | 4 | 15 | Search term only reaches ORM `icontains` lookups (parametrized); admin-only views, permissions unchanged |
| Code quality | 4 | 15 | ruff/pre-commit clean in both repos; ESM uses stock `search_fields` via `supp` M2M, custom code only where no relation exists; reviewer's unneeded-DISTINCT minor fixed (scratch `test_file_search_by_article_is_not_distinct` RED→GREEN) |
| Maintainability | 4 | 15 | `ArticleSearchMixin` limited to the 2 `File` admins; ESM search is declarative; no duplication |
| Error handling | 4 | 10 | Nullable `label` handled with explicit fallback to non-null `original_filename`; blank term short-circuits to stock behaviour |
| Documentation | 3 | 10 | Docstrings on mixin, method and `__str__`; CLAUDE.md advanced_admin description not yet updated (doc-sync next) |

## Recommendations
- Testing: if wjs-themes ever gains a suite, port `test_advanced_admin_scratch.py` cases into it.
- Documentation: mention the article-aware search in wjs-themes `CLAUDE.md` advanced_admin bullet.

## Total
**75%** — Correct, minimal fix; weaker on lasting test coverage because wjs-themes has no suite.
