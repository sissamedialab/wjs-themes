# Frozen-Author Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every author name across both themes link to the right `Account`, and never crash or emit a dead anchor when a frozen author has no account.

**Architecture:** Pure template change. Seven link sites in two themes converge on one spelling — link only when `FrozenAuthor.author` exists, otherwise render the name as plain text. No Python, no new component, no new dependency.

**Tech Stack:** Django templates, djLint (`djlint-django` via pre-commit), two Janeway themes (`wjs-bootstrap`, `JCOM-theme`).

**Spec:** [`docs/superpowers/specs/2026-09-17-frozen-author-links-design.md`](../specs/2026-09-17-frozen-author-links-design.md)

## Global Constraints

- The URL `articles_by_author` takes an **`Account` pk** (`<int:author>`, resolved with `get_object_or_404(Account, pk=...)`). Never pass a `FrozenAuthor` pk.
- `FrozenAuthor.author` is nullable (`null=True, on_delete=SET_NULL`). Every link site must tolerate `None`.
- Use the local column `author_id`, never `author` / `author.pk`: traversing the FK costs one SELECT per frozen author and nothing prefetches it (spec, Decision 4).
- Preserve each site's existing markup exactly: ORCID icons, comma/"and" separator logic, `{# djlint:off #}` / `{# djlint:on #}` regions, and `bootstrap_button` usage. Only the link condition changes.
- This repo has **no tests**. Do not add a test harness in this change (spec, Decision 3).
- Branch: `bugfix/issue-3048-fix-frozen-author-links`. Commit messages in English, Conventional Commits.

---

### Task 1: Converge all seven author links on the conditional form

**Files:**
- Modify: `wjs/themes/wjs-bootstrap/templates/journal/components/article_documents.html:45`
- Modify: `wjs/themes/JCOM-theme/templates/journal/components/article_documents.html:35`
- Modify: `wjs/themes/JCOM-theme/templates/journal/components/article_header.html:25`
- Modify: `wjs/themes/JCOM-theme/templates/elements/article_listing.html:25,48`
- Modify: `wjs/themes/wjs-bootstrap/templates/journal/components/article_listing.html:49`
- Modify: `wjs/themes/wjs-bootstrap/templates/journal/components/author_link.html:2`
- Test: none — see Global Constraints; verification is the probe + djlint + manual.

**Interfaces:**
- Consumes: `article.frozen_authors.all` (a `FrozenAuthor` queryset) and `FrozenAuthor.author` (nullable FK to `core.Account`), `FrozenAuthor.full_name`.
- Produces: no new names. The target pattern, applied at every site:

```django
{% if au.author_id %}<a href="{% url 'articles_by_author' au.author_id %}">{{ au.full_name }}</a>{% else %}{{ au.full_name }}{% endif %}
```

The loop variable is `au` in some templates and `author` in others — use whichever the surrounding loop already binds; do not rename it.

- [ ] **Step 1: Fix the two wrong-pk sites (the reported defect)**

In `wjs/themes/wjs-bootstrap/templates/journal/components/article_documents.html`, inside `{% for au in kid.frozen_authors.all %}`, replace:

```django
<a href="{% url 'articles_by_author' au.pk %}">{{ au.full_name }}</a>
```

with:

```django
{% if au.author_id %}<a href="{% url 'articles_by_author' au.author_id %}">{{ au.full_name }}</a>{% else %}{{ au.full_name }}{% endif %}
```

leaving the trailing `{# djlint:off #}...{# djlint:on #}` separator logic on the same line untouched. Apply the identical change in `wjs/themes/JCOM-theme/templates/journal/components/article_documents.html`.

- [ ] **Step 2: Fix the three unguarded sites (latent HTTP 500)**

Same substitution, in:
- `wjs/themes/JCOM-theme/templates/journal/components/article_header.html` — loop variable is `author`, and the link is followed by an ORCID block that must stay as it is.
- `wjs/themes/JCOM-theme/templates/elements/article_listing.html:48` — loop variable `au`, inside the `article.genealogy.children.all` loop.
- `wjs/themes/wjs-bootstrap/templates/journal/components/article_listing.html:49` — loop variable `au`, inside the `article|article_children` loop.

- [ ] **Step 3: Fix the two guarded sites (dead `<a href="">`)**

`wjs/themes/JCOM-theme/templates/elements/article_listing.html:25` currently assigns `{% url 'articles_by_author' author.author.pk as by_author %}` and renders `<a href="{{ by_author }}">` at line 31. Replace the assignment/anchor pair with the conditional anchor at the render site, and drop the now-unused `by_author` assignment.

`wjs/themes/wjs-bootstrap/templates/journal/components/author_link.html` renders through `bootstrap_button`. Keep that call for the linked case and render `{{ author.full_name }}` as plain text otherwise:

```django
{% if author.author_id %}
  {% url 'articles_by_author' author.author_id as author_url %}
  {% with "Go to all articles by "|add:author.full_name as aria_label_text %}
    {% bootstrap_button author.full_name href=author_url button_type="link" role="link" button_class="btn-link p-0" aria_label=aria_label_text %}
  {% endwith %}
{% else %}
  {{ author.full_name }}
{% endif %}
```

The ORCID and email blocks below it are unchanged and stay outside the conditional — they depend on `author.orcid` / `author.display_email`, not on the account.

- [ ] **Step 4: Verify no wrong-pk or unguarded spelling survives**

Run:

```bash
grep -rn "articles_by_author" --include="*.html" .
```

Expected: every hit passes `.author_id`, and every one is inside an `{% if ....author_id %}` guard. No occurrence of `au.pk`, `author.pk`, or any `.author.pk` relation traversal as the URL argument.

- [ ] **Step 5: Re-run the rendering probe against the final fragments**

Render the fixed pattern with a `FrozenAuthor` stand-in for both cases (`author` set, `author=None`) and confirm: correct `Account` pk for the linked case, plain text and no exception for the orphan case. Expected output shape:

```
conditional | linked              | <a href="/articles/author/42/">Jane Doe</a>
conditional | orphan(author=None) | Jane Doe
```

- [ ] **Step 6: Run pre-commit**

```bash
pre-commit run --all-files
```

Expected: PASS, in particular `djlint-django` (template linting) and `editorconfig-checker`. djLint is whitespace-sensitive around the `djlint:off` regions — if it reformats, re-read the diff and confirm the separator logic still renders commas and "and" in the right places.

- [ ] **Step 7: Commit**

Per the flow's commit-strategy decision.

```bash
git add wjs/themes
git commit -m "fix(themes): link author names to the right account, tolerate orphans

Refs specs#3048"
```

---

## Validation

- All seven sites converge on the conditional spelling (Step 4 grep).
- Probe output as in Step 5.
- `pre-commit run --all-files` clean.
- Manual check on a running environment: an article with child articles
  (`article_documents.html`), an article header, and a listing page.

## Out of scope

- Any test harness for this repo (spec, Decision 3) — recorded as a follow-up.
- Componentising the author link per theme (spec, Decision 5).
- The remaining `Article.authors` uses in `wjs-profile-project` ([!1510](https://gitlab.sissamedialab.it/wjs/wjs-profile-project/-/merge_requests/1510)).
