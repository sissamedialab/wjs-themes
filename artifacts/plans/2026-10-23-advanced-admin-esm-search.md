# Advanced admin ESM search — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the ESM changelist crash on label-less files and let advanced-admin file pages and
Article submission be searched by article identifier (e.g. `JCOM_4515`, `4515`) and title word.

**Architecture:** wjs-themes gets a `__str__` on `SupplementaryFileProxy` and an
`ArticleSearchMixin` that extends `ModelAdmin.get_search_results` with an `Article` subquery,
applied to four file admins. wjs-submission-project gets one more `search_fields` entry.

**Tech Stack:** Django 5.2 admin, Janeway `core`/`submission` models, pytest-django (wjs-submission
suite only).

**Spec:** `artifacts/specs/2026-10-23-advanced-admin-esm-search-design.md` (wjs-themes)

## Global Constraints

- Branch in both repos: `bugfix/issue-3198-advanced-admin-search`, from `wjs-develop`. Issue: wjs/specs#3198.
- No change to the Janeway fork.
- wjs-themes: ruff (line length 119), double quotes; public methods need docstrings (D102).
- wjs-submission-project: black/isort/flake8/pydocstyle, line length 119; no ruff.
- Docs, commit messages and branch names in English.
- Commits only at the end of the flow, after user review (no per-task commits).

## Review Focus

1. **Empty / whitespace-only search term** → behaves exactly like the stock admin (no extra
   query, full list). Test in Task 2.
2. **File with `article_id = NULL`** must not match an article search and must not error.
   Test in Task 2.
3. **Article with several identifiers matching the term** (e.g. `pubid` and `preprintid` both
   contain `4515`) → each file listed once. Test in Task 2.
4. **Multi-word title fragment** (`Interpreting the`) → matches as one substring, not AND of
   words. Test in Task 2.
5. **ESM whose file has both empty label and an article match** → listed without crashing
   (Task 1 `__str__` + Task 2 search together). Test in Task 2.

## Verification harness (wjs-themes)

wjs-themes has no test suite (`.claude/rules/tests.md`), so Tasks 1–2 use a **throwaway** pytest
file in the session scratchpad, run against wjs-submission-project's test infrastructure (which
already imports `wjs.advanced_admin.admin`, and wjs-themes is installed editable in the `janeway`
pyenv). It is never committed.

- Scratch file: `<scratchpad>/test_advanced_admin_scratch.py`, starting with
  `pytest_plugins = ["tests.conftest"]`, using the `journal`, `article`, `admin` fixtures.
- Run from `janeway/src` (needs user go-ahead — outside the repo boundary), with the local
  workarounds from memory `wjs-submission-local-pytest` (`-p no:freezegun`, scratch settings
  module with no-op `SkipMigrations.setdefault`, `--create-db` if stale):

  ```bash
  cd /Users/sfedoruk/Projects/sissa/janeway/src
  PYTHONPATH=../../wjs-submission-project:<scratchpad> \
    /Users/sfedoruk/.pyenv/versions/janeway/bin/python -m pytest -p no:freezegun \
    --ds=<scratch settings> --rootdir ../../wjs-submission-project \
    <scratchpad>/test_advanced_admin_scratch.py -v
  ```

Helper used in scratch tests: `_file(article_id, label=None, original_filename="esm.pdf") -> File`
creating `core.models.File(article_id=..., label=..., original_filename=..., uuid_filename="x.pdf")`.
Call admin search as `admin_obj.get_search_results(request, Model.objects.all(), term)` with
`request = RequestFactory().get("/")` and `request.user = admin`.

---

### Task 1: `SupplementaryFileProxy.__str__` (wjs-themes)

**Files:**
- Modify: `wjs/advanced_admin/admin.py:54-58` (`SupplementaryFileProxy`)
- Test: scratch file (see harness)

**Interfaces:**
- Produces: `SupplementaryFileProxy.__str__(self) -> str` = `self.file.label or self.file.original_filename`

- [ ] **Step 1: Write failing tests**

```python
def test_proxy_str_falls_back_to_original_filename(article):
    sf = SupplementaryFileProxy.objects.create(file=_file(article.pk, label=None, original_filename="data.zip"))
    assert str(sf) == "data.zip", "label-less ESM must display its original filename"

def test_proxy_str_uses_label_when_set(article):
    sf = SupplementaryFileProxy.objects.create(file=_file(article.pk, label="Dataset S1"))
    assert str(sf) == "Dataset S1", "labelled ESM must keep displaying its label"

def test_esm_changelist_renders_with_labelless_file(client, admin, article):
    SupplementaryFileProxy.objects.create(file=_file(article.pk, label=None))
    client.force_login(admin)
    url = reverse("advanced_admin:advanced_admin_supplementaryfileproxy_changelist")
    response = client.get(url, {"q": "esm"})
    assert response.status_code == 200, "changelist must not crash on label-less ESM"
```

(If the URL name differs, take it from `advanced_admin_site.get_urls()`; the changelist test may
need the journal request middleware — if it can't be made to render in the harness, keep the two
`str()` tests and cover rendering in the manual check.)

- [ ] **Step 2: Run — expect FAIL** (`TypeError: __str__ returned non-string` / `None != "data.zip"`)
- [ ] **Step 3: Add `__str__` to `SupplementaryFileProxy`** after `class Meta`, with a one-line docstring.
- [ ] **Step 4: Run — expect PASS**

> **Revision (2026-10-23, user decision after Task 2):** the ESM admins (`SupplementaryFileI`,
> `SupplementaryFileAutocompleteAdmin`) use plain `search_fields` via the reverse M2M `supp`
> (`supp__title`, `supp__identifier__identifier`) instead of the mixin; the mixin stays on
> `FileAdmin`/`FileAutocompleteAdmin` only, without `article_id_lookup`, and returns `super()`'s
> `may_have_duplicates`. See spec §B1/§B2. Text below is the original task as executed first.

> **Revision 2 (2026-10-23, after local real-data check):** the `supp` revision above is reverted —
> all four file admins use `ArticleSearchMixin` (ESM ones with `file__article_id`); the mixin also
> matches the article pk (`4050`, `JQuant_4050`); Article submission gets `=article__id` plus a
> label-to-digits rewrite. See spec "Revision 2".

### Task 2: `ArticleSearchMixin` on file admins (wjs-themes)

**Files:**
- Modify: `wjs/advanced_admin/admin.py` — add mixin near `FileSaveMixin`; apply to
  `FileAdmin` (~l.113), `SupplementaryFileI` (~l.140), `SupplementaryFileAutocompleteAdmin`
  (~l.342), `FileAutocompleteAdmin` (~l.362)
- Test: scratch file

**Interfaces:**
- Produces:
  - `class ArticleSearchMixin` with class attribute `article_id_lookup: str = "article_id"`
  - `get_search_results(self, request, queryset, search_term) -> tuple[QuerySet, bool]`
- Consumes: `Article` (already imported), `django.db.models.Q`

Algorithm (not determined by the signature):

```python
queryset_result, may_have_duplicates = super().get_search_results(request, queryset, search_term)
term = search_term.strip()
if term:
    article_ids = Article.objects.filter(
        Q(identifier__identifier__icontains=term) | Q(title__icontains=term)
    ).values("pk")
    queryset_result |= queryset.filter(**{f"{self.article_id_lookup}__in": article_ids})
    may_have_duplicates = True
return queryset_result, may_have_duplicates
```

Mixin goes **first** in the bases (`class FileAdmin(ArticleSearchMixin, admin.ModelAdmin)`).
`article_id_lookup = "file__article_id"` on the two `SupplementaryFile` admins.

- [ ] **Step 1: Write failing tests** (article gets `Identifier(id_type="preprintid", identifier="JCOM_4515")`
  and `title="Interpreting the signals of science"`; a second article with unrelated title/ids)

```python
def test_esm_search_by_preprintid(...):   # "4515" and "JCOM_4515" → ESM of article only
def test_esm_search_by_title_word(...):   # "Interpreting" → ESM of article only
def test_esm_search_multiword_title(...): # "Interpreting the" → ESM of article
def test_file_search_by_preprintid(...):  # FileAdmin, "4515" → files of article only
def test_search_ignores_files_without_article(...):  # File(article_id=None) never in result for "4515"
def test_search_no_duplicates_with_multiple_matching_identifiers(...):
    # add Identifier(id_type="pubid", identifier="JCOM_4515_2026_A01"); result after .distinct() count == 1
    # and may_have_duplicates is True
def test_empty_term_returns_all(...):     # "  " → same queryset count as .all(), may_have_duplicates False
def test_filename_search_still_works(...):# "data.zip" → that file (stock behaviour kept)
def test_autocomplete_admins_search_by_article(...): # both autocomplete admins, "4515" → article's files
```

Each assertion with a message, e.g. `assert set(qs) == {esm}, "4515 must find the ESM of JCOM_4515"`.

- [ ] **Step 2: Run — expect FAIL** (empty results for article terms)
- [ ] **Step 3: Implement the mixin and apply it** to the four admins
- [ ] **Step 4: Run — expect all scratch tests PASS** (Task 1 ones included)
- [ ] **Step 5: `pre-commit run --all-files`** in wjs-themes — expect pass

### Task 3: Article submission title search (wjs-submission-project)

**Files:**
- Modify: `wjs/plugins/wjs_submission/advanced_admin/advanced_admin.py:164`
  → `search_fields = ("article__identifier__identifier", "article__title")`
- Create: `tests/test_admin_article_submission_search.py`

- [ ] **Step 1: Write failing tests** (pattern: `tests/test_admin_access_mode.py`; admin instance
  `ArticleSubmissionAdmin(ArticleSubmission, django_admin.site)`)

```python
def test_article_submission_search_by_title_word(article, admin):
    # article.title = "Interpreting the signals of science"; ArticleSubmission.get_or_create(article=article)
    qs, _ = model_admin.get_search_results(request, ArticleSubmission.objects.all(), "Interpreting")
    assert submission in qs, "title word must find the article submission"

def test_article_submission_search_by_identifier_still_works(article, admin):
    # Identifier(id_type="preprintid", identifier="JCOM_4515") → "4515" finds it
```

- [ ] **Step 2: Run — expect title test FAIL, identifier test PASS**

```bash
cd /Users/sfedoruk/Projects/sissa/janeway/src
/Users/sfedoruk/.pyenv/versions/janeway/bin/python -m pytest -p no:freezegun --ds=<scratch settings> \
  ../../wjs-submission-project/tests/test_admin_article_submission_search.py -v
```

- [ ] **Step 3: Add `"article__title"` to `search_fields`**
- [ ] **Step 4: Run — expect PASS**; also run `tests/test_admin_access_mode.py tests/test_admin_affiliation.py` — expect PASS
- [ ] **Step 5: `pre-commit run --all-files`** in wjs-submission-project — expect pass

### Task 4: Manual check handoff

- [ ] Write the test-dev manual check list into the final summary: JQuant ESM search
  "supplementary" (no crash); JCOM ESM, "Manuscript files, ESM and admin files" and
  "Article submission" search `4515` and `Interpreting` (paper `JCOM_4515`, workflow 5410)
  return that paper's records.
