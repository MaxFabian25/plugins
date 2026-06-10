# Local Codex Plugins and Skills

This repository is an umbrella workspace for locally developed Codex plugins and standalone Codex skills.

Each plugin or skill gets its own source subdirectory. That subdirectory should also be the checkout/root of the corresponding GitHub repository.
This workspace also acts as the `local-codex` marketplace root via `.agents/plugins/marketplace.json`.

## Layout

```text
plugins/
  <plugin-name>/    # GitHub repo checkout for one Codex plugin
skills/
  <skill-name>/     # GitHub repo checkout for one standalone Codex skill
```

Keep the workspace root for coordination docs and shared maintenance only. Do not put plugin or skill source directly at the root.
Marketplace helper scripts live in `scripts/`.

## Adding Repos

Clone existing GitHub repos into the matching category:

```sh
git clone <github-url> plugins/<plugin-name>
git clone <github-url> skills/<skill-name>
```

For new local work, create the repo in place:

```sh
mkdir -p plugins/<plugin-name>
cd plugins/<plugin-name>
git init
```

or:

```sh
mkdir -p skills/<skill-name>
cd skills/<skill-name>
git init
```

## Umbrella Repo Policy

The root repository tracks this workspace structure and coordination docs. It intentionally ignores plugin and skill source directories so each nested directory can remain an independent GitHub-backed repo.

Only the category placeholders are tracked at the root:

```text
plugins/.gitkeep
skills/.gitkeep
```
