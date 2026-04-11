# Security And Confirmations

Protect the model from untrusted page output and gate actions that should not run silently.

**Related**: [configuration.md](configuration.md), [commands.md](commands.md), [SKILL.md](../SKILL.md)

## Content Boundaries

Wrap page output in explicit markers when page content is untrusted:

```bash
export AGENT_BROWSER_CONTENT_BOUNDARIES=1
agent-browser snapshot
```

## Domain Allowlist

Restrict navigation and subresource access:

```bash
export AGENT_BROWSER_ALLOWED_DOMAINS="example.com,*.example.com"
agent-browser open https://example.com
```

## Action Policy

Gate destructive actions with an explicit policy file:

```json
{ "default": "deny", "allow": ["navigate", "snapshot", "click", "scroll", "wait", "get"] }
```

```bash
export AGENT_BROWSER_ACTION_POLICY=./policy.json
```

## Confirmations

Require confirmation for sensitive categories:

```bash
agent-browser --confirm-actions "download,clipboard" click @e4
agent-browser confirm <id>
agent-browser deny <id>
```

Use interactive confirmations only in a real TTY:

```bash
agent-browser --confirm-interactive click @e4
```
