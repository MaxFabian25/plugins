# Debug And Observability

Use the lightest inspection surface that answers the current question.

**Related**: [commands.md](commands.md), [profiling.md](profiling.md), [video-recording.md](video-recording.md), [SKILL.md](../SKILL.md)

## Recommended Order

1. `snapshot -i`
2. `console`
3. `errors`
4. `network requests`
5. `trace` or `profiler`
6. `record`
7. `dashboard` and `stream`

## Console And Page Errors

```bash
agent-browser console
agent-browser errors
```

## Network Inspection

```bash
agent-browser network requests
agent-browser network request <requestId>
```

## Trace And Profiler

```bash
agent-browser trace start
agent-browser trace stop trace.zip
agent-browser profiler start
agent-browser profiler stop profile.json
```

## Video Recording

```bash
agent-browser record start flow.webm
agent-browser record stop
```

## Dashboard And Streaming

```bash
agent-browser dashboard start
agent-browser stream status
```
