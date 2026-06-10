# AGENTS.md

## Workspace Role

This directory is an umbrella workspace for locally developed Codex plugins and standalone Codex skills.

- Put each plugin repo under `plugins/<plugin-name>/`.
- Put each standalone skill repo under `skills/<skill-name>/`.
- Treat each plugin or skill source subdirectory as the root of its own GitHub-backed repository.
- Keep the umbrella root limited to coordination docs, shared maintenance, and workspace-level metadata.
- Do not put plugin or skill source directly at the umbrella root.

## Hard Cutovers Preference

Prefer hard cutovers; do not keep compatibility.

## Context7

Always use `ctx7` when library/API documentation, code generation, setup, or configuration steps are needed.

## `request_user_input`

Always call the `request_user_input` tool whenever intent or preference is remotely unclear.
