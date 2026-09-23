# Design: correct and harden the frozen-author links

**Issue:** [specs#3048 — Problems filtering by author in Vetrinetta](https://gitlab.sissamedialab.it/wjs/specs/-/work_items/3048)
(Priority 1, Size 2h, Sprint 26W36)

**Companion MR:** [wjs-profile-project!1510](https://gitlab.sissamedialab.it/wjs/wjs-profile-project/-/merge_requests/1510)
fixes the *view* side of the same issue (the author landing page filtered on the
deprecated `Article.authors` M2M instead of `FrozenAuthor`). This spec covers the
*template* side, found while reviewing that change.

**Status:** Root-cause analysis and fix approach, for approval before implementation.

## Context

Every author name on the public pages links to `/articles/author/<pk>/`, whose URL
pattern is `<int:author>` and whose view resolves the argument with
`get_object_or_404(Account, pk=...)`. The argument must therefore be an **`Account`
pk**.

All seven link sites in this repo iterate `article.frozen_authors.all` — i.e.
`FrozenAuthor` objects, not accounts. The account is reached through
`FrozenAuthor.author`, a nullable FK:

```python
# janeway/src/submission/models.py, class FrozenAuthor
author = models.ForeignKey(
    "core.Account", blank=True, null=True, on_delete=models.SET_NULL,
)
```

`null=True` is not theoretical: imported legacy articles routinely have frozen
authors with no corresponding account, and `on_delete=SET_NULL` actively creates
more whenever an `Account` is deleted.

## Root cause

Three different spellings of the same link have accumulated across the two themes,
and they behave differently. Rendered with Django's template engine against a
`FrozenAuthor` stand-in (`linked` = has an account, `orphan` = `author is None`):

| Spelling | Linked author | Orphan (`author=None`) |
| --- | --- | --- |
| `<a href="{% url 'articles_by_author' au.author.pk %}">` | `/articles/author/42/` ✅ | **`NoReverseMatch` → HTTP 500** |
| `{% url 'articles_by_author' au.author.pk as u %}` + `href="{{ u }}"` | `/articles/author/42/` ✅ | `<a href="">` — link to nowhere |
| `<a href="{% url 'articles_by_author' au.pk %}">` | `/articles/author/999/` ❌ | `/articles/author/999/` ❌ |

The third row is the defect originally reported: `au.pk` is the **`FrozenAuthor`**
pk, which is fed to a URL expecting an `Account` pk. It never raises — it silently
produces a plausible-looking link to whichever unrelated account happens to hold
that id, or a 404 when none does.

The first row is a latent 500: when Django cannot resolve `au.author.pk` it
substitutes `string_if_invalid` (empty string), and `reverse()` then rejects `''`
against an `<int:...>` converter.

### Where each spelling is used

**Wrong pk — `au.pk`** (2 sites, both the children-by-section listing):
- `wjs/themes/wjs-bootstrap/templates/journal/components/article_documents.html:45`
- `wjs/themes/JCOM-theme/templates/journal/components/article_documents.html:35`

**Unguarded — crashes on orphans** (3 sites):
- `wjs/themes/JCOM-theme/templates/journal/components/article_header.html:25`
- `wjs/themes/JCOM-theme/templates/elements/article_listing.html:48`
- `wjs/themes/wjs-bootstrap/templates/journal/components/article_listing.html:49`

**Guarded — degrades to an empty href** (2 sites):
- `wjs/themes/JCOM-theme/templates/elements/article_listing.html:25`
- `wjs/themes/wjs-bootstrap/templates/journal/components/author_link.html:2`

## Method

Adopt one spelling everywhere: link only when the frozen author actually has an
account, and otherwise render the name as plain text.

```django
{% if au.author_id %}<a href="{% url 'articles_by_author' au.author_id %}">{{ au.full_name }}</a>{% else %}{{ au.full_name }}{% endif %}
```

This is correct for all three current failure modes: right pk, no `NoReverseMatch`,
and no anchor pointing at nothing. Author names remain visible in every case — only
the hyperlink is conditional.

The whole conditional stays on **one line**. Most of these links are immediately
followed by a `{# djlint:off #}` region carrying the comma/"and" separator logic, and
any newline between `{% endif %}` and that region would render as whitespace before
the comma.

Existing markup around each link (ORCID icons, comma/"and" separators, the
`djlint:off` regions, `bootstrap_button` in `author_link.html`) is preserved as-is.

## Decisions

### 1. Conditional link rather than the guarded `{% url ... as %}` form

The `as` form already in the codebase prevents the crash, so it is the smaller
change. It is rejected as the target pattern because it leaves `<a href="">` in the
output — an anchor that re-navigates to the current page, which is a user-visible
defect of its own and an accessibility problem. Conditioning the anchor costs two
extra template lines per site and produces correct output in every case.

### 2. All seven sites, not just the reported two

Fixing only `article_documents.html` would leave three templates able to return a
500 on legacy content and two rendering dead anchors — three different behaviours
for the same concept across two themes. The whole family is small (7 sites, one
pattern) and is best reviewed once.

### 3. No test infrastructure introduced

This repo has **no tests at all** — no `pytest.ini`, no test files, no test job in
`.gitlab-ci.yml`. Standing up a Django template-rendering harness to cover a
template fix would be a far larger change than the fix, and would need decisions
(settings module, fixtures, CI job) that belong to the team rather than to a
Priority-1 maintenance issue.

Verification is therefore: the rendering probe already run against all three
spellings (recorded above), `djlint-django` via pre-commit, and manual checks on a
running environment. Introducing a test harness is recorded as a follow-up.

### 4. `author_id`, not `author` — no extra queries

The guard and the URL argument both use the local column `au.author_id` rather than
traversing the relation with `au.author` / `au.author.pk`.

Traversing the FK costs **one SELECT per frozen author**: Django's
`ForwardManyToOneDescriptor.__get__` fetches the related object on a cache miss, and
nothing prefetches `frozen_authors__author` on these pages. Using `.author_id` reads
an integer already present on the `FrozenAuthor` row — zero queries.

This matters most at the two `article_documents.html` sites: they previously used
`au.pk` and issued **no** query at all, so guarding on `au.author` would have traded
a correctness bug for a new N+1 on exactly the collection pages this issue is about
(a collection of 30 children × 4 authors would add ~120 queries per render). Using
`author_id` also removes the *pre-existing* N+1 at the other five sites.

Trade-off accepted: if the column ever pointed at a deleted `Account`, `.author_id`
would render a link that 404s where `.author` would have degraded to plain text. The
FK is `on_delete=SET_NULL` with database-level enforcement, so the row cannot dangle.

### 5. Not componentised

`wjs-bootstrap` already has a reusable `author_link.html`; `JCOM-theme` has no
equivalent and its markup differs (plain `<a>` and inline ORCID icons versus
`bootstrap_button`). Unifying them is a refactor with its own review surface and
is out of scope here — the fix keeps each site's markup and changes only the link
condition.

## Implementation

Per template, replace the link expression with the conditional form, preserving the
surrounding separators and `djlint:off` comments exactly. Order: the two `au.pk`
sites first (the reported defect), then the three unguarded sites, then the two
guarded sites.

## Validation

- Re-run the rendering probe on the final template fragments, confirming: correct
  `Account` pk for linked authors, plain text and no exception for orphans.
- `pre-commit run --all-files` — in particular `djlint-django` and
  `editorconfig-checker`.
- Manual check on a running environment: an article with child articles
  (`article_documents.html`), an article header, and a listing page — each with at
  least one author whose `FrozenAuthor.author` is NULL, if such content can be
  reached.

## Known style debt

Five of the touched lines now exceed the 240-character `max_line_length` that
`.editorconfig` declares for `[*.html]` (272–312 chars; none exceeded it before).
This is not a CI failure — `.editorconfig-checker.json` sets
`"Disable": {"MaxLineLength": true}`, and `.claude/rules/templates-django.md`
records why. It is accepted deliberately: the conditional cannot be wrapped without
injecting whitespace before the separator commas (see *Method*).

## Follow-ups (not done here)

- No test infrastructure in this repo. A minimal template-rendering test harness
  would have caught all three spellings. Worth its own work item, and worth sizing
  honestly: the probe used to validate this change is ~60 lines of
  `settings.configure()` plus `Template().render()`, with no database and no Janeway
  import — a small ticket, not a week of work.
- Record the canonical author-link spelling in `.claude/rules/templates-django.md`,
  under the conventions djlint does not check. Three spellings accumulated precisely
  because none was written down.
- `author_link.html` loads `i18n` but never uses it, and its aria-labels
  ("Go to all articles by …", "Send an email to …") are hardcoded English in a repo
  shipping `en`/`es`/`pt` locales. Pre-existing; noticed while adding the `{% else %}`
  branch.
- Consider a shared author-link component per theme, so this cannot drift into
  three spellings again.
- `wjs-profile-project`: the remaining `Article.authors` uses listed in
  [!1510](https://gitlab.sissamedialab.it/wjs/wjs-profile-project/-/merge_requests/1510).
