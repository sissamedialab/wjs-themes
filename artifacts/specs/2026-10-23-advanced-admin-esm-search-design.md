# Advanced admin: ESM `__str__` crash and search by article — design

- **Issue:** wjs/specs#3198
- **Repos:** `wjs-themes` (main), `wjs-submission-project` (one-line change)
- **Branch (both repos):** `bugfix/issue-3198-advanced-admin-search`, from `wjs-develop`
- **Status:** approved 2026-10-23

## Problem

Reported on test-dev (JQuant, JCOM) in the advanced admin:

1. **ESM changelist crashes** for some searches (e.g. "supplementary" on JQuant) with
   `TypeError: __str__ returned non-string (type NoneType)`.
2. **Files of a paper cannot be found** by paper ID or title word. Example: paper
   `JCOM_4515` (`/plugins/wjs-review-articles/status/5410/`, title starting with
   "Interpreting…"). Searching `4515` or `Interpreting` on the ESM page returns nothing; the
   same happens on "Manuscript files, ESM and admin files" and on "Article submission".

## Root cause

### 1. `__str__` returns `None`

- Janeway `core.models.SupplementaryFile.__str__` returns `self.file.label`.
- `core.models.File.label` is `null=True, blank=True`, so ESM whose file has no label return
  `None` from `__str__`.
- Django 5's changelist renders the `action_checkbox` column with `aria-label=str(obj)` for
  every row, so any changelist page containing a label-less ESM crashes. The search term
  only matters because it decides which rows are on the page.

### 2. Search does not know about articles

Current `search_fields` in the advanced admin:

| Admin page | Model admin | Searched fields | Article ID | Title |
|---|---|---|---|---|
| ESM | `SupplementaryFileI` (wjs-themes) | `file__original_filename`, `doi` | no | no |
| Manuscript files, ESM and admin files | `FileAdmin` (wjs-themes) | `original_filename`, `label`, `description` | no | no |
| Article submission | `ArticleSubmissionAdmin` (wjs-submission) | `article__identifier__identifier` | yes | no |

`File.article_id` is a plain `PositiveIntegerField`, not a foreign key, so
`search_fields` cannot traverse to `Article` (no `file__article__title`).

## Decisions

- **No Janeway change.** The `__str__` fix lives on the wjs-themes proxy only (decided by the
  user). Known limit: the Article change page `supplementary_files` autocomplete and the
  `SupplementaryFile` autocomplete endpoint still use Janeway's base `__str__` and can still
  fail for label-less ESM. Out of scope.

## Design

### A. `SupplementaryFileProxy.__str__` (wjs-themes)

```python
def __str__(self):
    return self.file.label or self.file.original_filename
```

`original_filename` is a required field, so the result is always a string. Fixes the ESM
changelist, change page title/breadcrumbs, and delete confirmation.

> **Revision 2 (2026-10-23, after local check on real data) — supersedes §B1 and extends §B2/§C:**
>
> - `JQuant_4050` / `JCOM_4515` shown in wjs-review is **not** an `Identifier`: it is built on the fly
>   as `f"{article.journal.code}_{article.pk}"` (`wjs_review/states.py`). Search must match the
>   article **pk**.
> - On the local DB 798 of 917 `SupplementaryFile` are **not** in any `Article.supplementary_files`,
>   while 912 have `file.article_id`. §B1 (`supp__…`) misses most ESM, so it is dropped: the ESM admins
>   use `ArticleSearchMixin` again with `article_id_lookup = "file__article_id"`.
> - `ArticleSearchMixin` also matches `pk` exactly when the term is `<digits>` or `<word>_<digits>`
>   (regex `(?:\w+?_)?(\d+)`), on top of identifier/title `icontains`. Bare numbers stay broad
>   (identifier substring) — user's choice.
> - Article submission (wjs-submission): `"=article__id"` added to `search_fields`, plus a
>   `get_search_results` that rewrites a `<word>_<digits>` label to its digits. No dependency on the
>   wjs-themes mixin, so the two packages release independently.

### B1. Search ESM by article (wjs-themes) — plain `search_fields` *(superseded, see Revision 2)*

`SupplementaryFile` is reachable from `Article` through the real M2M
`Article.supplementary_files` (`related_name="supp"`), so the ESM admins just add
`"supp__title"` and `"supp__identifier__identifier"` to `search_fields`:

- `SupplementaryFileI` (ESM page)
- `SupplementaryFileAutocompleteAdmin` (ESM picker on the Article change page)

ESM are therefore matched by the article they are attached to, not by `file.article_id`.
Stock admin search splits the term into words and ANDs them across fields.

### B2. Search files by article (wjs-themes) — `ArticleSearchMixin`

`File` has no relation to `Article` at all (only the integer `article_id`), so a small mixin
overrides `ModelAdmin.get_search_results`:

1. Run the default search (`super().get_search_results(...)`).
2. If the term is non-empty, find matching article ids:
   `Article.objects.filter(Q(identifier__identifier__icontains=term) | Q(title__icontains=term))`
   — this matches `JCOM_4515`, `4515`, and title words like `Interpreting`.
3. OR the result with `queryset.filter(article_id__in=article_ids)`.
4. Return `super()`'s `may_have_duplicates` unchanged: an `IN` subquery on a single-valued
   column cannot duplicate rows, so no extra `DISTINCT` is needed.

The term is used as one string (not split per word) so a multi-word title fragment works.

Applied to `FileAdmin` (Manuscript files, ESM and admin files) and `FileAutocompleteAdmin`.

*Revised 2026-10-23 after review: originally the mixin covered the ESM admins too via
`file__article_id`; the user chose plain `search_fields` where a real relation exists.*

### C. Article submission title search (wjs-submission-project)

Add `"article__title"` to `ArticleSubmissionAdmin.search_fields`.

## Verification

- wjs-themes has **no automated test suite** (`.claude/rules/tests.md`). Verification:
  - a one-off Red→Green script run with Janeway's interpreter (proxy `__str__` with a
    label-less file; `get_search_results` by preprint id and by title word);
  - manual check on test-dev: JQuant ESM search "supplementary"; JCOM ESM / Files search
    `4515` and `Interpreting`.
- wjs-submission-project: add a test in its suite for title search on `ArticleSubmissionAdmin`
  if an advanced-admin test module exists; otherwise manual check.
- `pre-commit run --all-files` in both repos.

## Out of scope

- Fixing `SupplementaryFile.__str__` in the Janeway fork.
- Changing what is displayed in the list columns.
