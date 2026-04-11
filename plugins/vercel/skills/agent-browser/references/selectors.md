# Selectors

Choose the smallest selector surface that keeps the interaction reliable.

**Related**: [snapshot-refs.md](snapshot-refs.md), [commands.md](commands.md), [SKILL.md](../SKILL.md)

## Default Order

1. `@e` refs from `snapshot -i`
2. semantic locators such as `find role`, `find label`, `find text`, `find placeholder`
3. CSS selectors only when the page already exposes a stable hook

## Refs First

```bash
agent-browser open https://example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
```

## Semantic Locators

```bash
agent-browser find role button click --name "Sign in"
agent-browser find label "Email" fill "user@example.com"
agent-browser find placeholder "Search" type "agent-browser"
```

## CSS Selectors

Use CSS only when the page already exposes something stable:

```bash
agent-browser click "#submit-button"
agent-browser wait "[data-testid='dashboard']"
```

## `snapshot -i --urls`

When you need to inspect links without clicking through and back:

```bash
agent-browser snapshot -i --urls
```

## Visual Fallback

When layout or unlabeled icon buttons matter:

```bash
agent-browser screenshot --annotate
```
