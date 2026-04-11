# Configuration

Persistent config, environment variables, and safe defaults for agent-browser.

**Related**: [commands.md](commands.md), [security-and-confirmations.md](security-and-confirmations.md), [SKILL.md](../SKILL.md)

## Config Precedence

Agent-browser resolves config in this order, lowest to highest priority:

1. `~/.agent-browser/config.json`
2. `./agent-browser.json`
3. environment variables
4. CLI flags

## Minimal Project Config

```json
{
  "headed": false,
  "screenshotFormat": "png",
  "downloadPath": "./downloads"
}
```

## Safer Agent Config

```json
{
  "contentBoundaries": true,
  "allowedDomains": "example.com,*.example.com",
  "maxOutput": 30000
}
```

## Boolean Override Rule

CLI boolean flags can override config values directly:

```bash
agent-browser --headed
agent-browser --headed false
```

## Useful Environment Variables

```bash
export AGENT_BROWSER_SESSION=docs-check
export AGENT_BROWSER_DOWNLOAD_PATH="$PWD/downloads"
export AGENT_BROWSER_CONTENT_BOUNDARIES=1
export AGENT_BROWSER_ALLOWED_DOMAINS="example.com,*.example.com"
export AGENT_BROWSER_MAX_OUTPUT=30000
```

## Common Check

Use this when config behavior seems wrong:

```bash
agent-browser --help
cat ./agent-browser.json
env | rg '^AGENT_BROWSER_'
```
