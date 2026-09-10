# 🐑 mLoop Herdr Plugin

Official **mLoop Orchestrator Plugin for Herdr (v0.8.2+)**.

## Features
- **Sprint Backlog Split View** : Split pane to monitor vertical stories and INVEST criteria.
- **EvidencePack Overlay** : Quick popup / overlay to inspect sidecar `memory/evidence/` JSON logs.
- **Live DAG Monitor** : Real-time visualization of multi-agent orchestration events (`memory/herdr_events.jsonl`).
- **Anti-Zombie Cleaner Action** : Purge orphan or dead worker panes instantly.

## Installation

### Local Link
```bash
herdr plugin link plugins/mloop-herdr-plugin
```

### Manifest Declaration
See `herdr-plugin.toml`.
