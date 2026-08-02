# Police-Thief P2P — Distributed Cops-and-Robbers over a Peer-to-Peer Network

Final project, "Orchestration of AI Agents" — Dept. of Computer Science, University of Haifa, 2026.

Two autonomous agents — **cop** and **thief** — race on a discrete grid with **no central server
and no referee**: P2P over FastMCP, SHA-256 commit-reveal integrity, decaying pheromone scent
fields, Bayesian belief maps, deceptive natural-language hints, a local-truth GUI, and a
cryptographic Replay Viewer.

> **Status: in development.** This README will become the full academic report at submission
> (Dec-POMDP model, orchestration dilemmas, strategies, screenshots, companion-repo link).

## Quick start (will be kept current)

```bash
uv sync

# Terminal 1
uv run python -m police_thief peer --role police
# Terminal 2
uv run python -m police_thief peer --role thief

# Replay a saved match
uv run python -m police_thief replay --log logs/log_<game_id>_g01.json

# Tests & lint
uv run pytest
uv run ruff check .
```

## Documentation

| Document | Purpose |
|---|---|
| [docs/PRD.md](docs/PRD.md) | Product requirements (master) |
| [docs/PLAN.md](docs/PLAN.md) | Architecture, C4 model, ADRs |
| [docs/TODO.md](docs/TODO.md) | Task tracking & milestone gates |
| docs/PRD_*.md | Dedicated PRD per mechanism (7 files) |
| [docs/PROMPTS.md](docs/PROMPTS.md) | Prompts book (AI-assisted development log) |

## Configuration

Shared, signed game contract: `config/game.json` (values mirror the rulebook's Mandatory
Parameters Table; byte-identical on both peers, locked via SHA-256). Private per-peer settings:
`config/police/game.toml`, `config/thief/game.toml` (overlay rule: shared JSON overrides).
Secrets live in `.env` / `credentials.json` / `token.json` — all git-ignored; see `.env-example`.

## License & credits

MIT (see LICENSE). Built with FastMCP, google-api-python-client, Anthropic API. Reference
implementation consulted: rmisegal/Game-P2P-Cop-Chase (educational-use license).
