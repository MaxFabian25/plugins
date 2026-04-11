# Diffing

Verify that an action actually changed the page instead of assuming success.

**Related**: [snapshot-refs.md](snapshot-refs.md), [commands.md](commands.md), [SKILL.md](../SKILL.md)

## Snapshot Diff

Use this after an interaction that should change the accessibility tree:

```bash
agent-browser snapshot -i
agent-browser click @e2
agent-browser diff snapshot
```

## Screenshot Diff

Use this for visual regressions:

```bash
agent-browser screenshot baseline.png
agent-browser diff screenshot --baseline baseline.png
```

## URL Diff

Use this when comparing two environments or routes:

```bash
agent-browser diff url https://staging.example.com https://prod.example.com --screenshot
```

## Recommended Rule

If the task says “verify”, do not stop at `click` or `fill`. Capture a baseline, perform the action, and use a diff or a targeted postcondition.
