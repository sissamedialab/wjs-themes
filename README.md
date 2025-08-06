# Janeway themes for WJS

Package for wjs-specific templates

It currently provides:

- JCOM-Theme: legacy "Vetrinetta theme" derived from "material" Janeway theme
- wjs-bootstrap: bootstrap-based theme for both vetrinetta and backoffice dashboard

It's available as a standard python package (not as a Janeway plugin) for easier installation and distribution.

## Install

See [Janeway Setup](https://gitlab.sissamedialab.it/wjs/specs/-/wikis/setup-janeway) and
[migration guide](https://gitlab.sissamedialab.it/wjs/specs/-/wikis/migrate-wjs-submission) for installation instructions.

## Commands

### Helper scripts

- `build_assets.sh`: Watch for css / js changes to rebuild theme assets

## Usage

### wjs-bootstrap

Available both as a Janeway theme and as plain django template repository (for usage with wjs application strictly based on `wjs-bootstrap` templates).

#### Using as Janeway theme

Select as "Journal Theme" in `http://<journal-domain>/manager/settings/journal/`

#### Using as standard django template

Extend templates from `wjs/base/base.html`

#### Working with stylesheets

Stylesheets are located in `wjs/themes/wjs-bootstrap/assets/sass`.

When developing, run `build_assets.sh` to watch for changes and rebuild assets.

### JCOM-Theme

Janeway sub-theme, it's only available for journal it's been selected.

To enable it for a journal select as "Journal Theme" in `http://<journal-domain>/manager/settings/journal/`
