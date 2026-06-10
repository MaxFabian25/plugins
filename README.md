# Local Codex Plugins

This repository is an umbrella workspace for locally developed Codex plugins.

Each plugin gets its own source subdirectory. That subdirectory should also be the checkout/root of the corresponding GitHub repository.
This workspace also acts as the `local-codex` marketplace root via `.agents/plugins/marketplace.json`.

Standalone Codex skills live separately in `/Users/maxibon/Documents/Maximilian's-codex-skills` and `MaxFabian25/skills`.

## Layout

```text
plugins/
  <plugin-name>/    # GitHub repo checkout for one Codex plugin
```

Keep the workspace root for coordination docs and shared maintenance only. Do not put plugin source directly at the root.
Marketplace helper scripts live in `scripts/`.

## Adding Repos

Clone existing GitHub repos into the matching category:

```sh
git clone <github-url> plugins/<plugin-name>
```

For new local work, create the repo in place:

```sh
mkdir -p plugins/<plugin-name>
cd plugins/<plugin-name>
git init
```

## Umbrella Repo Policy

The root repository tracks this workspace structure and coordination docs. It intentionally ignores plugin source directories so each nested directory can remain an independent GitHub-backed repo.

Only the plugin category placeholder is tracked at the root:

```text
plugins/.gitkeep
```
