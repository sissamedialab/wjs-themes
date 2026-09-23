# Evaluation — frozen-author-links

- **Date:** 2026-09-17
- **Branch:** `bugfix/issue-3048-fix-frozen-author-links` (working tree, no commits yet)
- **Task:** [specs#3048](https://gitlab.sissamedialab.it/wjs/specs/-/work_items/3048) — template half; view half is [wjs-profile-project!1510](https://gitlab.sissamedialab.it/wjs/wjs-profile-project/-/merge_requests/1510)
- **Coverage:** full — 6 templates (7 link sites), `.claude/rules/templates-django.md`, plus the untracked spec and plan

## Priority findings

- **Testing (2):** no automated coverage of any kind. This repo has no test infrastructure — no `pytest.ini`, no test files, no CI test job — so nothing will catch a regression here. Verification rests on a grep over call sites, a standalone rendering probe of extracted fragments, and `djlint`. Deliberate (spec, Decision 3) and defensible for a P1 template fix, but it is the weakest part of this change and the manual check on a running environment is still outstanding.

## Scores

| Dimension | Score | Weight | Key evidence |
|---|---|---|---|
| Functionality | 4 | 20 | All three failure modes fixed at 7/7 sites; probe shows linked → `/articles/author/42/`, orphan → plain text, no exception. Caveat: the probe renders fragments copied from the templates, not the templates in context. |
| Testing | 2 | 15 | No tests exist or were added. Red→green was demonstrated only via the standalone probe comparing old and new fragments. |
| Security | 4 | 15 | `{{ au.full_name }}` is autoescaped in the new `{% else %}` branch, as it was inside the anchor before — no escaping change. Removes a public-page 500 path (`NoReverseMatch`), which is mildly positive. |
| Code quality | 4 | 15 | One consistent spelling across two themes; `pre-commit run --all-files` clean (20 hooks, incl. `djlint-django`). Debt: 5 lines now exceed `.editorconfig`'s declared 240-char HTML ceiling (272–312), unenforced and documented. |
| Maintainability | 3 | 15 | The conditional is duplicated at 7 sites with no component and no test to catch drift — the same conditions that let three spellings accumulate. Mitigated only by the new convention entry in `.claude/rules/templates-django.md`. |
| Error handling | 4 | 10 | The change *is* the error-handling fix: an unhandled `NoReverseMatch` becomes deliberate graceful degradation to plain text. Rough edge: orphans lose the `btn-link` styling in `author_link.html` and one SCSS `a` selector. |
| Documentation | 5 | 10 | Spec and plan saved and amended after review (query cost, line-length debt, single-line constraint, three follow-ups); canonical spelling recorded in the repo's own rules file. `CHANGELOG.md` correctly untouched — it is release-generated. |

## Recommendations

- **Testing:** file the template-rendering harness follow-up and size it honestly — the probe used here is ~60 lines of `settings.configure()` + `Template().render()`, no DB, no Janeway import. It is a small ticket, and it would have caught all three spellings.
- **Maintainability:** revisit componentisation once a harness exists; a per-theme `author_link.html` used everywhere would make this unrepeatable.

## Total

**73%** — a correct, complete fix that also removes a pre-existing N+1, documented unusually well; dragged down by a repo with no way to test it and by seven copies of one pattern.
