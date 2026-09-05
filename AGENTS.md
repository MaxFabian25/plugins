# AGENTS.md

## Workspace Role

This directory is an umbrella workspace for locally developed Codex plugins.

- Put each plugin repo under `plugins/<plugin-name>/`.
- Treat each plugin source subdirectory as the root of its own GitHub-backed repository.
- Keep the umbrella root limited to coordination docs, shared maintenance, and workspace-level metadata.
- Standalone Codex skills live in `/Users/maxibon/Documents/Maximilian's-codex-skills` and `MaxFabian25/skills`.

## Hard Cutovers Preference

Prefer hard cutovers; do not keep compatibility.

## Code and tests

Before keeping an abstraction or extension point, identify its current caller and the behavior
that needs it. Remove duplicate capabilities and controls used only by tests. Each test should
catch a meaningful failure through an actual interface that another retained check would miss.
Assert the required result, not source text, internal call order, or incidental fixture formatting.
For a simplification, verify the affected acceptance conditions and keep the diff within their
causal path.

## Documentation

Consult authoritative documentation when an API or configuration decision needs verification.
Prefer `ctx7` when it provides the relevant documentation. Use the local source or official
documentation directly when it already answers the question or the tool is unavailable.

## `request_user_input`

Ask when missing information materially affects the requested result or a consequential choice
cannot be inferred from the conversation. Resolve routine, reversible choices using the available
context and continue the work already authorised.
