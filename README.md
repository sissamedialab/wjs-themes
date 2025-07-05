# Janeway themes for WJS

Package for wjs-specific templates

It currently provides:

- JCOM-Theme: legacy "Vetrinetta theme" derived from "material" Janeway theme
- wjs-bootstrap: bootstrap-based theme for both vetrinetta and backoffice dashboard

It's available as a standard python package (not as a Janeway plugin) for easier installation and distribution.

## Installation

`pip install wjs-themes`

(it requires SISSA gitlab package repository to be available)

## Configuration

- Add `"wjs.themes"` in `INSTALLED_APPS` (this is already included in `wjs.defaults.settings`)


## Commands

### Django commands

- `install_themes`: Link themes in proper Janeway directory to make it available system-wide

### Helper scripts

- `build_assets.sh`: Watch for css / js changes to rebuild theme assets

## Usage

### wjs-bootstrap

Available both as a Janeway theme and as plain django template repository (for usage with wjs application strictly based on `wjs-bootstrap` templates).

#### Using as Janeway theme

Select as "Journal Theme" in `http://<journal-domain>/manager/settings/journal/`

#### Using as standar django template

Extend templates from `wjs/base/base.html`

### JCOM-Theme

Janeway sub-theme, it's only available for journal it's been selected.

To enable it for a journal select as "Journal Theme" in `http://<journal-domain>/manager/settings/journal/`
