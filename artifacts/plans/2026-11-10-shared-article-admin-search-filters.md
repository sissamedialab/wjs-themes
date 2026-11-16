# Shared article search and filters in the advanced admin — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Articles, Article submissions and a new Article workflows page in the advanced admin share one search (incl. accent-insensitive names / title and `<CODE>_<pk>` labels) and one set of filters; the new page lets the EO edit the workflow state, with a warning.

**Architecture:** A mixin in wjs-themes (`wjs/advanced_admin/admin.py`) builds `search_fields` / `list_filter` from an article lookup prefix and adds unaccent + pk-label matching in `get_search_results`. wjs-submission enables the PostgreSQL `unaccent` extension (migration) and switches `ArticleSubmissionAdmin` to the mixin; its test suite also covers wjs-themes' `ArticleAdmin` (wjs-themes has no test suite). wjs-profile registers a proxy-model `ArticleWorkflow` admin on `advanced_admin_site`.

**Tech Stack:** Django 5.2 admin, PostgreSQL `unaccent` (`django.contrib.postgres`), django-fsm `FSMField`, pytest-django.

**Spec:** `wjs-themes/artifacts/specs/2026-11-10-shared-article-admin-search-filters-design.md`

**Branch (all three repos):** `feature/issue-3329-shared-article-admin-filters` (already created from `origin/wjs-develop`).

## Global Constraints

- wjs-themes and wjs-submission code must not import `wjs_review`; the workflow-state filter is added in `get_list_filter()`.
- Search matches: article pk (bare `4050` or label `JCOM_4050`, exact), title, `identifier__identifier`, correspondence author email / first name / last name, owner email / first name / last name.
- Accent-insensitive (both column and term go through `unaccent`): title, first names, last names only. Emails and identifiers: plain `icontains`.
- Filters, in this order: journal, stage, workflow state, is import, peer reviewed, date submitted, date accepted, date declined, date published.
- `<CODE>_<pk>` returns the union: pk match **and** identifier `icontains` match; the code part is not checked against the journal.
- Article workflows page: list + change only (no add, no delete); `state` editable, article and `latest_state_change` read-only; warning text on the change form; saving does a raw field write (no transition, no log, no `latest_state_change` update).
- No permission migration (advanced admin is superuser-only in practice — spec, *Decisions*).
- Line length 119, double quotes, `gettext_lazy` for user-facing strings, docstrings on public methods.
- Running tests locally happens from `janeway/src` (outside the repos): ask the user for go-ahead before the first run. Known local workarounds: memory note `wjs-submission-local-pytest` (`-p no:freezegun`, scratch settings with a no-op `MIGRATION_MODULES.setdefault`, `--create-db` once).

## Review Focus

1. **Multi-word terms** (`signals of science`): Django splits the term into words and ANDs them; each word must still match through the unaccent fields → test in Task 2.
2. **Accented stored value, plain typed term and the reverse** (`Rudzinski` ↔ `Rudziński`, lowercase `rudzinski`) → tests in Task 2.
3. **Empty / whitespace term**: returns the whole queryset, no extra query, no crash → test in Task 2.
4. **Paper with no correspondence author** (nullable FK) is still found by title (OR across nullable joins must not drop it) → test in Task 2.
5. **Paper with two identifiers both matching the term** appears once on the changelist (`may_have_duplicates` honoured, union with the pk filter does not duplicate) → test in Task 2.

---

### Task 1: Enable `unaccent` (wjs-submission migration + test DB setup)

**Files:**
- Create: `wjs-submission-project/wjs/plugins/wjs_submission/migrations/0025_unaccent_extension.py`
- Modify: `wjs-submission-project/tests/conftest.py` (add session fixture)
- Modify: `wjs-profile-project/wjs/jcom_profile/tests/conftest.py` (same fixture; it is star-imported by `wjs_review/tests/conftest.py`)
- Test: `wjs-submission-project/tests/test_admin_article_search.py` (new)

**Interfaces:**
- Produces: the `unaccent` extension exists in prod (migration) and in every test DB (fixture). Test settings skip migrations (`SkipMigrations`), so the migration alone does not reach the test DB.

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.django_db
def test_unaccent_extension_available():
    """The unaccent extension is installed in the test database."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT unaccent(%s)", ["Rudziński"])
        assert cursor.fetchone()[0] == "Rudzinski", "unaccent must strip diacritics"
```

- [ ] **Step 2: Run it, expect FAIL** (`function unaccent(unknown) does not exist`)

Run (from `janeway/src`): `python -m pytest ../../wjs-submission-project/tests/test_admin_article_search.py -k unaccent -p no:freezegun --create-db`

- [ ] **Step 3: Migration** `0025_unaccent_extension.py`: `dependencies = [("wjs_submission", "0024_rename_use_of_ai_field")]`, `operations = [UnaccentExtension()]` (`django.contrib.postgres.operations`).

- [ ] **Step 4: Session fixture** in both conftests:

```python
@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Install the unaccent extension: test settings skip migrations, so 0025 never runs here."""
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
```

- [ ] **Step 5: Run the test, expect PASS.** Also `python manage.py migrate wjs_submission` on the local dev DB, then `python manage.py makemigrations wjs_submission --check --dry-run` shows no new changes for wjs_submission.

- [ ] **Step 6: Commit** (per the commit strategy chosen at flow start) — `feat(advanced_admin): enable the unaccent extension`

### Task 2: Shared mixin in wjs-themes, used by `ArticleAdmin`

**Files:**
- Modify: `wjs-themes/wjs/advanced_admin/admin.py` (new mixin + helper; `ArticleAdmin` uses it; `ArticleSearchMixin` reuses the shared regex)
- Test: `wjs-submission-project/tests/test_admin_article_search.py` (wjs-themes is installed in that suite; it has no suite of its own)

**Interfaces:**
- Produces (in `wjs.advanced_admin.admin`):
  - `ARTICLE_PK_RE = re.compile(r"(?:\w+?_)?(\d+)")` — module constant; `ArticleSearchMixin.article_pk_re` points to it.
  - `def unaccent_term(term: str) -> str` — returns `SELECT unaccent(%s)` of the term.
  - `class ArticleSearchFilterMixin`:
    - `article_lookup_prefix: str = ""` (`"article__"` for related models)
    - `workflow_state_lookup: str | None = None` → `None` means `f"{prefix}articleworkflow__state"`
    - `def get_search_fields(self, request) -> list[str]` — prefixed: `identifier__identifier`, `title__unaccent`, `correspondence_author__email`, `correspondence_author__first_name__unaccent`, `correspondence_author__last_name__unaccent`, `owner__email`, `owner__first_name__unaccent`, `owner__last_name__unaccent`
    - `def get_list_filter(self, request) -> list[str]` — prefixed `journal`, `stage`, then the workflow-state lookup, then prefixed `is_import`, `peer_reviewed`, `date_submitted`, `date_accepted`, `date_declined`, `date_published`
    - `def get_search_results(self, request, queryset, search_term)` — empty / blank term → `super()` unchanged; otherwise `super()` with `unaccent_term(term)`, then `|` `queryset.filter(**{f"{prefix}pk": n})` when `ARTICLE_PK_RE.fullmatch(term.strip())`. Returns super's `may_have_duplicates`.
  - The pk is **not** in `search_fields` (avoids integer casting of text terms and substring pk matches).

- [ ] **Step 1: Write the failing tests** against `wjs.advanced_admin.admin.ArticleAdmin` (`Article.objects.all()`, `_search` helper as in `test_admin_article_submission_search.py`). Fixture: article with title `Interpreting the signals of science`, identifier `JCOM_4515`, correspondence author `Marta Rudziński <m.rudzinski@example.org>`, owner `William Munizzi <munizziwilliam@example.org>`.
  - `test_article_search_finds[term]` parametrized, each asserts `article in result`: `"{pk}"`, `"JQuant_{pk}"`, `"JCOM_4515"`, `"Interpreting"`, `"signals of science"`, `"m.rudzinski@example.org"`, `"Rudziński"`, `"Rudzinski"`, `"rudzinski"`, `"Marta"`, `"Munizzi"`, `"munizziwilliam@example.org"`, `"William"`.
  - `test_article_search_stored_plain_typed_accented` — owner last name `Rudzinski`, term `Rudziński` → found.
  - `test_article_search_pk_is_exact` — `f"9{pk}9"` → not found.
  - `test_article_search_label_also_matches_identifier` — second article with pk ≠ 4515 and identifier `JCOM_4515`; term `JCOM_4515` → that article found (and, if an article with pk 4515 exists, it too).
  - `test_article_search_blank_term_returns_all` — `"  "` → queryset equal to input.
  - `test_article_search_no_correspondence_author` — `correspondence_author=None`, term `Interpreting` → found.
  - `test_article_changelist_no_duplicates` — two identifiers `JCOM_4515` and `JCOM_4515_v2` on one article; `admin_client` GET on the advanced admin changelist `?q=JCOM_4515` → `response.context["cl"].result_count == 1`. URL: `reverse("admin:submission_article_changelist", current_app="advanced_admin")`.
  - `test_article_list_filter` — `ArticleAdmin(...).get_list_filter(request) == ["journal", "stage", "articleworkflow__state", "is_import", "peer_reviewed", "date_submitted", "date_accepted", "date_declined", "date_published"]`.

- [ ] **Step 2: Run, expect FAIL** (name / email / unaccent / filter assertions).

- [ ] **Step 3: Implement** the helper, constant and mixin; `ArticleAdmin(ArticleSearchFilterMixin, FileSaveMixin, admin.ModelAdmin)`; drop its `search_fields` attribute and its `get_list_filter` override. `ArticleSearchMixin.article_pk_re = ARTICLE_PK_RE` (File / ESM behaviour unchanged).

- [ ] **Step 4: Run the new tests + `test_admin_article_submission_search.py`, expect PASS.** wjs-submission must resolve wjs-themes from the local checkout (editable install in the janeway env — verify with `pip show -f wjs-themes` before trusting a green run).

- [ ] **Step 5: `pre-commit run --all-files` in wjs-themes, expect PASS.**

- [ ] **Step 6: Commit** in wjs-themes — `feat(advanced_admin): share article search and filters across article pages`

### Task 3: `ArticleSubmissionAdmin` uses the mixin

**Files:**
- Modify: `wjs-submission-project/wjs/plugins/wjs_submission/advanced_admin/advanced_admin.py:147-196`
- Modify: `wjs-submission-project/setup.cfg` (`wjs-themes >= 2.1.11`)
- Test: `wjs-submission-project/tests/test_admin_article_submission_search.py`

**Interfaces:**
- Consumes: `ArticleSearchFilterMixin` from Task 2.

- [ ] **Step 1: Extend the tests** with the same parametrized `test_article_submission_search_finds[term]` list as Task 2 (on `ArticleSubmissionAdmin` / `ArticleSubmission.objects.all()`) and `test_article_submission_list_filter` expecting the Task 2 list with the `article__` prefix on every entry (state → `article__articleworkflow__state`). Keep the existing tests.

- [ ] **Step 2: Run, expect FAIL.**

- [ ] **Step 3: Implement:** `class ArticleSubmissionAdmin(ArticleSearchFilterMixin, admin.ModelAdmin)` with `article_lookup_prefix = "article__"`; remove `list_filter`, `search_fields`, `get_search_results`, `get_list_filter` and the now-unused `re` import. Bump `wjs-themes >= 2.1.11` in `setup.cfg`.

- [ ] **Step 4: Run the whole wjs-submission admin tests (`tests/test_admin_*.py`), expect PASS.** Then the full wjs-submission suite once; the known local failure `test_views.py::test_submission_author_only[False]` is pre-existing.

- [ ] **Step 5: `pre-commit run --all-files` in wjs-submission, expect PASS.**

- [ ] **Step 6: Commit** in wjs-submission (Task 1 + Task 3 changes, or two commits per the strategy) — `feat(advanced_admin): share article search and filters on article submissions`

### Task 4: Article workflows page in wjs-profile

**Files:**
- Modify: `wjs-profile-project/wjs/plugins/wjs_review/advanced_admin/admin.py` (proxy + admin)
- Modify: `wjs-profile-project/setup.cfg` (`wjs-themes >= 2.1.11`, `wjs-submission >= 2.1.9`)
- Test: `wjs-profile-project/wjs/plugins/wjs_review/tests/test_advanced_admin_article_workflow.py` (new)

**Interfaces:**
- Consumes: `ArticleSearchFilterMixin` (Task 2), `unaccent` in the test DB (Task 1 fixture).
- Produces: `ArticleWorkflowProxy` (`verbose_name = _("Article workflow")`, `verbose_name_plural = _("Article workflows")`), `ArticleWorkflowAdmin` on `advanced_admin_site` with `article_lookup_prefix = "article__"`, `workflow_state_lookup = "state"`. No migration for the proxy (existing advanced-admin proxies have none).

- [ ] **Step 1: Write the failing tests** (fixtures from `jcom_profile/tests/conftest.py`: `admin`, `submitted_article`, `client`):
  - `test_article_workflow_search_finds[term]` — subset: `"{pk}"`, `"JCOM_{pk}"`, title word, correspondence author last name typed without accents, owner email.
  - `test_article_workflow_list_filter` — Task 2 list with `article__` prefix, state entry `"state"`.
  - `test_article_workflow_changelist_and_change_page` — admin GET on `admin:wjs_review_articleworkflowproxy_changelist` and `..._change` (`current_app="advanced_admin"`) → 200; change page contains the warning text.
  - `test_article_workflow_state_saved` — POST the change form with `state=ArticleWorkflow.ReviewStates.WITHDRAWN` → 302; `workflow.refresh_from_db().state == "Withdrawn"`; `latest_state_change` unchanged.
  - `test_article_workflow_no_add_no_delete` — `has_add_permission` and `has_delete_permission` are `False` for the admin user.

- [ ] **Step 2: Run, expect FAIL** (`NoReverseMatch` / import error).

- [ ] **Step 3: Implement** the proxy and admin:
  - `list_display`: article title, label (`<journal code>_<pk>`, reuse the existing `pubid`/label helper if wjs_review has one), journal, `state`; `ordering = ("-pk",)`.
  - Change form: `fieldsets` with one fieldset `("article", "state", "latest_state_change")`, `readonly_fields = ("article", "latest_state_change")`, `description` = the warning (`gettext_lazy`):
    "Changing the state here only updates the state field. It does not run the workflow transition: no log entry, no notifications, no changes to assignments, reminders or attention conditions. Use only to fix a paper that is stuck."
  - `has_add_permission` / `has_delete_permission` → `False`.
  - Bump `setup.cfg` requirements.

- [ ] **Step 4: Run the new test module, expect PASS;** then `wjs_review/tests/test_blacklisted_author.py` (other advanced admin tests) still pass.

- [ ] **Step 5: `pre-commit run --all-files` in wjs-profile, expect PASS.**

- [ ] **Step 6: Commit** in wjs-profile — `feat(wjs_review): add article workflows page to the advanced admin`

### Task 5: Manual check on the local dev instance

- [ ] **Step 1:** `python manage.py migrate` (applies `wjs_submission.0025`), run the dev server, log in as a superuser EO.
- [ ] **Step 2:** Run the spec's functional test steps 2–5 on Articles, Article submissions, Article workflows with a local paper whose owner / correspondence author has a diacritic in the last name (pick one from the DB; create none if one exists). Record results for the issue comment.
