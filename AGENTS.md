# AGENTS.md

## Workspace Role

This directory is an umbrella workspace for locally developed Codex plugins.

- Put each plugin repo under `plugins/<plugin-name>/`.
- Treat each plugin source subdirectory as the root of its own GitHub-backed repository.
- Keep the umbrella root limited to coordination docs, shared maintenance, and workspace-level metadata.
- Do not put plugin source directly at the umbrella root.
- Standalone Codex skills live in `/Users/maxibon/Documents/Maximilian's-codex-skills` and `MaxFabian25/skills`.

## Hard Cutovers Preference

Prefer hard cutovers; do not keep compatibility.

## Documentation

Consult authoritative documentation when an API or configuration decision needs verification.
Prefer `ctx7` when it provides the relevant documentation. Use the local source or official
documentation directly when it already answers the question or the tool is unavailable.

## `request_user_input`

Ask when missing information materially affects the requested result or a consequential choice
cannot be inferred from the conversation. Resolve routine, reversible choices using the available
context and continue the work already authorised.
