# Advanced admin: shared search and filters for article pages — design

- **Issue:** wjs/specs#3329 (epic #2853, related #3198, #2983)
- **Repos:**
  - `wjs-themes` — shared mixin, Article page (main)
  - `wjs-submission-project` — Article submissions page, `unaccent` migration
  - `wjs-profile-project` — new Article workflows page
- **Branch (all three repos):** from `wjs-develop`, name decided at branch creation
- **Status:** approved 2026-11-10

## Intent

In the advanced admin the EO finds a paper on one article page but not on another, because
each page searches and filters different fields. All three article pages must search and
filter the same way, so the EO can move between them without guessing. The EO also needs an
"Article workflows" page in the advanced admin to change a paper's state, which today is
only possible in the standard Django admin (`/admin/`).

Tester feedback on the issue (2026-11-05, JQuant / JCOM test-dev) lists searches that must
work: `JQuant_4365`, a title word (`coherent`), the correspondence author's email, the
owner's last name — including `Rudziński` typed both as `Rudziński` and as `Rudzinski` —
and, on Article submissions, the owner's last name and the correspondence author's email.

## Goals

1. **Same search on the three pages** (Articles, Article submissions, Article workflows).
   The search box matches:
   - article pk, bare (`4050`) or as the wjs-review label `<journal code>_<pk>`
     (`JCOM_4050`, `JQuant_4365`) — exact pk match, not substring;
   - title;
   - identifier / preprint ID (`identifier__identifier`);
   - correspondence author email, first name, last name;
   - owner email, first name, last name.
2. **Accent-insensitive search** on title and on first / last names: `Rudzinski` and
   `Rudziński` both find a stored `Rudziński`, and `Rudziński` finds a stored `Rudzinski`.
   Case-insensitive as today. Emails and identifiers are matched as today (no unaccent).
3. **Same filters on the three pages:** journal, stage, workflow state, is import, peer
   reviewed, date submitted, date accepted, date declined, date published. Filtering by
   journal + workflow state gives the same papers on all three pages.
4. **New "Article workflows" page** in the advanced admin, listing papers with the shared
   search / filters, where the EO can change a paper's workflow state and save.

## Non-goals

- The standard Django admin (`/admin/`) pages for Article, ArticleSubmission and
  ArticleWorkflow — unchanged.
- Other advanced admin pages (files, ESM, reviewer reports, editor reports, cover letters…).
- Running the workflow transition logic when the state is changed from the admin.

## Anti-goals

- wjs-themes or wjs-submission must not import or require `wjs_review`: their CI does not
  install it. The workflow-state filter stays added at runtime (`get_list_filter()`), as today.
- The state change must not pretend to be a transition: no partial side effects (no emails,
  no half-closed assignments). It is a raw field edit, clearly labelled as such.

## Decisions taken with the user

- **State change = raw edit with a warning (option A).** The new page edits
  `ArticleWorkflow.state` directly, exactly as `/admin/` already allows (`FSMField` is not
  `protected`; both admin sites use the same `is_staff` + model-permission checks). No log
  entry, no `latest_state_change` update, no notifications, no change to assignments,
  reminders, attention conditions or `article.stage`. The page shows a visible warning that
  says this. Restricting target states and extra safeguards (log entry,
  `latest_state_change`) were considered and rejected for this issue.
- **Accent-insensitive search is in scope**, via the PostgreSQL `unaccent` extension.
- **Documentation language:** English.
- **Permissions:** no permission migration or manual grant for the new proxy model. Checked
  on the local DB (2026-11-10): 27 accounts in the `EO` group, 20 superusers, 7 neither staff
  nor superuser (they cannot open any admin site, advanced or not); no non-superuser staff
  account exists and the `EO` group has no model permissions. Advanced admin access is
  therefore superuser-only in practice, and superusers get the new proxy's permissions
  implicitly — same as the existing proxies (Editor reports, Reviewer reports…).

## How (decided in the issue)

- Shared code in **wjs-themes**, `wjs/advanced_admin/admin.py`, next to
  `advanced_admin_site`: a mixin that builds `search_fields` / `list_filter` from an article
  lookup prefix — `""` for Article, `"article__"` for ArticleSubmission and ArticleWorkflow.
- Workflow-state filter added in `get_list_filter()`, not in the class attribute, so
  wjs-themes / wjs-submission CI does not need `wjs_review`. Its lookup is
  `articleworkflow__state` (Article), `article__articleworkflow__state` (ArticleSubmission),
  `state` (ArticleWorkflow).
- Reuse or align with the existing `<journal code>_<pk>` parsing (`ArticleSearchMixin.
  article_pk_re` in wjs-themes, the regex in `ArticleSubmissionAdmin.get_search_results`) —
  one implementation, used by the three pages.
- New ArticleWorkflow admin registered on `advanced_admin_site` in wjs-profile
  `wjs/plugins/wjs_review/advanced_admin/admin.py`, on a proxy model with a readable verbose
  name ("Article workflow" / "Article workflows"), like the other pages there.

## My calls (the user can override)

- **Where `unaccent` is enabled:** a migration in `wjs_submission` using
  `django.contrib.postgres.operations.UnaccentExtension` (`CREATE EXTENSION IF NOT EXISTS`).
  wjs_submission is installed wherever the advanced admin runs and its CI has PostgreSQL 17,
  so its tests can exercise unaccent search. wjs-themes has no models / migrations and no
  test suite. `django.contrib.postgres` is already in Janeway's `INSTALLED_APPS`.
  Deploy note for the MR: `unaccent` is a trusted extension since PostgreSQL 13, so the DB
  owner can create it; on older servers it needs a superuser — flag under *Required
  actions* (migrations, possibly manual DB step).
- **Unaccent both sides:** the stored column and the search term go through `unaccent`, so
  accents typed by the EO do not break matches. Applied to title and first / last name
  fields only.
- **Article workflows page content:** list shows paper (title / label), journal, state;
  change form shows the article read-only, `state` editable, `latest_state_change`
  read-only; no add, no delete. The warning is shown on the change form (fieldset
  description or form help text), worded roughly: "Changing the state here only updates the
  state field. It does not run the workflow transition: no log entry, no notifications, no
  changes to assignments, reminders or attention conditions. Use only to fix a paper that is
  stuck."
- **Article page:** keeps its current list columns and change form; only search and filters
  change. The existing `get_list_filter()` override is replaced by the mixin's.
- **Article submissions page:** same — only search and filters change; the label-parsing
  `get_search_results` override is replaced by the shared one.
- **Tests:** wjs-submission suite covers the mixin through `ArticleSubmissionAdmin` (search
  by each field, label pk, accent-insensitive names, filters present). wjs-profile suite
  covers the Article workflows page (registered, search, filters incl. state, state saved
  from the change form, no add / delete). wjs-themes Article page: manual check on test-dev
  (no test suite there, per its `.claude/rules/tests.md`).
- **Which papers each page lists:** each page lists its own rows (Article, ArticleSubmission,
  ArticleWorkflow); no rows are created and Articles is not narrowed. Imported / legacy papers
  without an ArticleSubmission or ArticleWorkflow row show only on the pages that have them.
  "Same results on the three pages" means: same papers among those that exist on each page.
- **`<CODE>_<pk>` that is also an identifier:** return the union, as the File / ESM search
  already does — the paper with that pk *and* papers whose identifier contains the term. The
  journal-code part is not checked against the paper's journal (unchanged behaviour). The
  File / ESM pages keep their current `ArticleSearchMixin` behaviour; they may share the
  parser if it does not change their results.
- **Spec location:** this document lives in wjs-themes (main repo for the shared code).

## Left to the builder

- Exact mixin name and API, how the prefix is applied, how unaccent lookups are combined
  with Django's `search_fields` machinery (e.g. `search_fields` plus an override of
  `get_search_results`).
- How `may_have_duplicates` / `distinct()` is handled for the identifier join.
- Exact warning wording and placement, list columns ordering.

## Functional test steps

From the issue, plus the tester's cases:

1. As EO on test-dev, open the advanced admin.
2. On "Articles": search `4050`, `JCOM_4050`, a preprint ID, a title fragment, a
   correspondence author email, an owner last name, and `Rudzinski` / `Rudziński` for a
   paper whose owner is `Rudziński`. Each finds the paper.
3. Repeat on "Article submissions" and "Article workflows": same results.
4. On each page the filter sidebar has journal, stage, workflow state, is import, peer
   reviewed, date submitted / accepted / declined / published; journal + workflow state
   gives the same papers on the three pages.
5. On "Article workflows", open a test paper: the warning is visible; change the state and
   save. The new state shows in the list and on the paper page in wjs-review.
6. Repeat 2–4 on another journal.
