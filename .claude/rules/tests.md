# Testing rules

**This repo has no automated test suite.** There is no `tests/` directory, no
`[tool.pytest.ini_options]` (or any other pytest config) in `pyproject.toml`, no `pytest`/
`pytest-django` dependency anywhere in `setup.cfg`, and no `docker-compose-test-*.yml` files.
Don't port pytest invocations, fixture conventions, or coverage targets from sibling `wjs-*`
repos (e.g. `wjs-submission-project`) — they don't apply here.

> **Note for anyone porting rules from another `wjs-*` repo:** this repo is a themes/templates
> package, distributed as a **standard Python package, not a Janeway plugin** (see the top-level
> `README.md`). There is no `wjs/plugins/wjs_submission/`-style layout to symlink into Janeway's
> `plugins/` folder, and the installed package name is `wjs-themes` (`setup.cfg`), not
> `wjs-submission`.

## How changes actually get verified

Because there's no test suite, verification is manual, inside a running Janeway checkout that has
this package installed (editable) alongside it:

1. Install this package editable into Janeway's virtualenv (`pip install -e .` from this repo).
2. From `janeway/src`, run `python manage.py install_themes` (provided by
   `wjs/themes/management/commands/install_themes.py`) to symlink `wjs-bootstrap`/`JCOM-theme`
   into Janeway's `themes/` directory and apply `wjs/install/settings.json`.
3. For SCSS/template changes, run `build_assets.sh` from this repo (assumes a sibling
   `../janeway` checkout) to compile assets and watch for further changes — see
   `.claude/rules/linting.md`/top-level `CLAUDE.md` for details.
4. Select the theme on a journal (`http://<journal-domain>/manager/settings/journal/`) and check
   the affected pages/templates render correctly in the browser.

There is no CI job that exercises this package's templates or Python code beyond linting
(`.gitlab-ci.yml`'s `Pre-commit` job — see `.claude/rules/linting.md`); a change here is only
proven correct by that manual check inside Janeway, not by a green test run.

## If a real test suite is ever added

Should this repo ever get automated tests, follow the generic conventions used across `wjs-*`
repos rather than inventing new ones:

- Test files: `test_<module>.py`; test functions: `test_<description>`; fixtures in `conftest.py`.
- Use descriptive assertions — no bare `assert` without a message.
- Unit tests mock external services and test logic in isolation; integration tests use a real
  database and never mock the Django ORM.
- Update this file with the actual settings module, invocation command, and directory used —
  don't assume they'll match `wjs-submission-project`'s.
