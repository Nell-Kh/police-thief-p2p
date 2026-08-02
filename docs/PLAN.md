# PLAN — Architecture & Technical Design

**Project:** police-thief-p2p | **Version:** 1.00 | **Status:** awaiting approval
Companion to docs/PRD.md. Binding values live in `config/game.json` (mirror of Rulebook Appendix ו).

---

## 1. C4 Model

### 1.1 Context (C1)

```
+----------------+        natural-language hints,        +----------------+
|  POLICE peer   | <--- commits/reveals over MCP  ---->  |   THIEF peer   |
| (our process A)|        via public tunnel URLs         | (our process B |
+-------+--------+                                       |  or opponent)  |
        |                                                +--------+-------+
        | Gmail API (send-only, JSON attachment)                  |
        v                                                         v
+-------+---------+     game-end reports      +--------------------------+
| Lecturer inbox  | <------------------------ |  Anthropic API (Haiku)   |
| rmisegal+uoh26  |                           |  verbal layer only       |
+-----------------+                           +--------------------------+
```

### 1.2 Containers (C2) — one per peer process

Each peer (police, thief) is one Python process composed of: Tkinter GUI (local truth only),
FastMCP server (inbound tools), MCP client (outbound calls), the Orchestrator runtime, and
file-based storage (config/, logs/, results/). A separate Replay Viewer process loads saved logs.

### 1.3 Components (C3) — inside a peer

```
GUI / CLI  ─────────┐            (no business logic in this layer)
                    v
            +---------------+
            | SDK (sdk.py)  |  single business entry point
            +-------+-------+
                    v
            +---------------+     services/ (Orchestrator layer)
            | Orchestrator  |──> GamePhaseMachine (state machine)
            | (gateway)     |──> DeadlineTracker   ──> Watchdog
            +-------+-------+──> PeerRuntime (turn loop)
                    v
   domain/ (pure logic, no I/O)         infra/ (I/O adapters)
   board  rules  scoring  scent          mcp_server  mcp_client
   belief brain  crypto  protocol        llm providers  email sender
   negotiation  audit  logbook           tunnel helpers
                    v
   shared/: config manager, gatekeeper(+token bucket, quota, DOS), version
```

Rules honored: Orchestrator is the only coordinator (no peripheral module knows another);
strategy module plugs into PeerRuntime **after hint decode, before commit pack**; all external
API calls pass through the Gatekeeper; every file ≤ 150 code lines.

### 1.4 Code (C4) — package layout

```
src/police_thief/
├── __init__.py  __main__.py  constants.py
├── sdk/sdk.py                      # SimulationSdk - facade for GUI/CLI/tests
├── domain/
│   ├── board.py rules.py scoring.py        # stage 1
│   ├── scent.py belief.py trust.py         # stage 4
│   ├── crypto.py step0.py audit.py         # stage 6
│   ├── protocol.py negotiation.py logbook.py
│   └── brain/ (base.py heuristic.py police.py thief.py pathfind.py)
├── services/ (orchestrator.py phase_machine.py deadline.py watchdog.py runtime.py)
├── infra/
│   ├── mcp_server.py mcp_client.py
│   ├── llm/ (base.py template.py ollama.py claude_api.py claude_cli.py)
│   └── email/ (sender.py oauth.py reports.py)
├── gui/ (live.py heatmap.py banner.py replay.py)   # excluded from coverage
└── shared/ (config.py gatekeeper.py bucket.py version.py sysinfo.py)
```

## 2. Key state machine (mandatory rules #4/#5)

TRANSITIONS = WAITING_FOR_OPPONENT→{COMPUTING_MOVE}; COMPUTING_MOVE→{COMMITTING,TECHNICAL_LOSS};
COMMITTING→{AWAITING_REVEAL}; AWAITING_REVEAL→{VERIFYING,TECHNICAL_LOSS}; VERIFYING→
{WAITING_FOR_OPPONENT}; TECHNICAL_LOSS→∅ (terminal). Illegal transition ⇒ immediate exception.

## 3. Turn sequence (UML-style)

```
Police                                Thief
  | compute move (brain)                |
  | COMMIT: H=SHA256(canonical record) →|  ack ────────────────────────┐
  |←────────────── COMMIT (thief's H)   |                              |
  | ack ────────────────────────────────→                              |
  | REVEAL: move+hint (nonce hidden)   →|  verify vs H, update belief  |
  |←────────────── REVEAL               |                              |
  | apply physics, decay scent, GUI     |  same                        |
  | ... at game end: FINAL REVEAL of all nonces + mutual audit ────────┘
```

## 4. Data contracts

- **Shared signed:** `config/game.json` (schema_version 1.2) — board_and_agents, world,
  movement_and_barriers, scoring, pheromones, network_and_league, rate_limiter_gatekeeper.
  Canonical JSON (sorted keys, fixed separators) hashed to `config_sha256`; play refused on
  mismatch. Per-game copies named `config_<game_id>_g<NN>.json` (mandatory rule, Appendix ו.2).
- **Private:** `config/police/game.toml`, `config/thief/game.toml` — [game], [network],
  [strategy], [trash_talk], [llm], [email]. Overlay rule: shared JSON overrides parallel keys.
- **Commit record (canonical JSON):** {state, move, intent, hint, step, role, sub_game, nonce}
  → SHA-256 hex. Nonce: `secrets.token_hex(16)`; comparisons via `secrets.compare_digest`.
- **Lifecycle files:** declaration_<game_id>.json (Step-0: teams, members, repos, hardware, LLM,
  token cap, github_commit, times, signature), config_…, log_…_g<NN>.json (per-step commits,
  reveals, hints, nonces at end), result_<game_id>.json (per-mini-game scores + totals) —
  attached to the report email.

## 5. Architectural Decision Records (ADR)

- **ADR-1 Single dev repo, split at submission.** The rulebook mandates two submitted repos
  (cop, thief). We develop in one repo for velocity and shared-engine correctness (mirroring the
  reference implementation's layout), then generate the two submission repos with per-role
  configs, docs and history before tagging `v1.0-submission`. Trade-off: extra split step vs.
  avoiding double-maintenance of mirrored engine code during development. Runtime separation is
  preserved throughout (two processes, `config/police/` vs `config/thief/`, no shared state).
- **ADR-2 Enhanced heuristic strategy (no RL).** Bayesian belief + barrier-aware BFS distances +
  trust-weighted hint fusion + cop barrier planning. Transparent, testable, zero training cost;
  RL explicitly optional and not course material. Alternative considered: Q-Learning — rejected
  for training/runtime risk with no grade requirement.
- **ADR-3 Verbal layer via claude_api (Haiku) with template fallback.** Meets the user's choice
  of richer banter; hard fallback to the zero-token template provider on any API failure or
  budget exhaustion guarantees every mini-game finishes (fallback pattern from the reference
  research report). `every_n_steps=3` throttles spend against the ~200k series budget.
- **ADR-4 Axis convention.** Top-left origin, (row, col), 0-indexed, y grows downward (ch. 3
  default). The ch. 6 figure's y-up convention is documented as illustrative only.
- **ADR-5 Tkinter for GUI.** Stdlib (no extra dependency), sufficient for heatmap + banner +
  replay controls; GUI excluded from coverage per guidelines' omit list, logic kept in domain.
- **ADR-6 Canonical-JSON commit payload.** Conceptual formula covers 4 fields; we seal the
  richer reference record (adds hint, step, role, sub_game) for interop and stronger binding.

## 6. Deployment

Local dev: two terminals — `uv run python -m police_thief peer --role police|thief` on ports
8801/8802. League: each peer exposed via ngrok/Localtonet public URL placed in the opponent's
TOML `opponent_url`. Secrets (`credentials.json`, `token.json`, `.env`) never leave the machine.

## 7. Traceability

Every mandatory rule of Rulebook Appendix ה (#1–#55) and every MANDATORY item of the guidelines
maps to a module + test in docs/COMPLIANCE.md (produced at M8 and kept current from M6).
