# PRD — Distributed Cops-and-Robbers over a Peer-to-Peer Network

**Project:** police-thief-p2p | **Version:** 1.00 | **Status:** awaiting approval
**Course:** Orchestration of AI Agents, Dept. of Computer Science, University of Haifa — Final Project 2026
**Governing documents:** Rulebook v3.0.0 (Dr. Yoram Segal) and "Guidelines for Writing Professional Software at the Highest Level of Excellence" v3.00. Where this PRD and the rulebook disagree, the rulebook and its Mandatory Parameters Table (Appendix ו) prevail.

---

## 1. Overview and Context

Two autonomous, symmetric agents — a **cop (police)** and a **thief** — play a pursuit race on a
discrete grid **with no central server and no referee**. Each agent runs as an independent peer:
simultaneously an MCP **server** (FastMCP) and an MCP **client** of its opponent. Neither agent ever
sees the true world state; each maintains a probabilistic **belief map** of its opponent's position,
fed by the opponent's decaying **scent field** and a **verbal hint that may be a lie**. Integrity
without a judge is achieved cryptographically: every move passes a **SHA-256 commit-reveal**
protocol, and a full **mutual log audit** at game end exposes any forgery (technical loss).

The system is formally a **Dec-POMDP** ⟨n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ⟩ with n=2: the transition
function P and reward R are pinned by a cryptographically signed shared configuration
(`config/game.json`), and each agent's observation Ωᵢ is restricted to local truth (own position,
opponent's scent field, received hints).

**User problem.** Course students must field an agent that can coordinate, adapt, stay honest, and
survive real network conditions against opponents built by other teams in a live league — then
prove all of it in an auditable, reproducible submission.

**Target audience.** The lecturer/grader (primary), the opposing teams (peers in the league), and
the team itself (development and research).

## 2. Goals, KPIs and Acceptance Criteria

| Goal | KPI / acceptance criterion |
|---|---|
| Legal, complete game engine | Full mini-game runs end-to-end without crash; all scoring rules of rulebook ch. 3 enforced; 100% of illegal moves rejected |
| True P2P over MCP | Two separate processes complete a full game via FastMCP over a public URL (tunnel), not only localhost |
| Cryptographic integrity | Commit-reveal active on every step; end-of-game audit passes; Replay Viewer shows **Verified OK**; any tamper → **TAMPERED** + disqualification |
| Uncertainty handling | Scent emission/decay per locked model; Bayesian belief map computed each turn and demonstrably drives movement |
| Reliability | State machine rejects illegal transitions; deadline tracker + watchdog produce controlled TECHNICAL_LOSS instead of hangs |
| League readiness | Automatic JSON end-of-game report sent via Gmail API (send-only scope) by our side, through the Gatekeeper |
| Engineering quality | 0 ruff violations; test coverage ≥ 85% (fail_under=85); every code file ≤ 150 lines; uv-only workflow |
| Submission | Two GitHub repos (cop, thief) with cross-links, academic README, screenshots (belief map + Verified OK), tag `v1.0-submission`; ≥ 2 league games against different teams |

## 3. Functional Requirements

FR are grouped by subsystem; each has a dedicated PRD (see §7) with detailed I/O and test scenarios.

1. **Board & physics engine** — grid of `grid_size` (≥7×7), orthogonal moves + STAY, no diagonals;
   cop-only barrier placement (turn without movement, self or 4-adjacent cell, quota `max_barriers`,
   irreversible, publicly declared); capture by coordinate overlap + Capture Claim, by trapping
   placement, or by thief having no legal move; survival win at `survival_threshold` valid steps;
   scoring 20/5 (capture cop/thief), 5/10 (survival cop/thief), tie 2, technical loss 0/0.
2. **P2P communication** — FastMCP server + client per peer; tools for negotiation, commit,
   acknowledge, reveal, hint delivery, capture claim, audit exchange; tunneling (ngrok/Localtonet)
   for league play; MCP standard may not be replaced.
3. **Commit-reveal cryptography** — per step: Commit (SHA-256 over canonical JSON of
   state/move/intent/hint/step/role/nonce), Acknowledge, Reveal (nonce still secret), end-of-game
   Final Reveal of all nonces + mutual audit; `secrets`-grade nonces; constant-time comparison;
   Step-0 signed hardware + git-commit-hash + token-budget declaration before move 1.
4. **Scent & belief** — 5×5 emission field (center 0.9, fixed radial matrix), per-turn decay
   τ(t+1)=max(0,(1−ρ)τ+Δτ) with ρ=0.10; per-side scent history; Bayesian belief map fusing scent
   evidence with trust-weighted verbal hints; lie detection by expected-vs-measured scent.
5. **Strategy module** — separate module plugged in between hint-decode and commit-pack;
   `BrainBase` with `_pick_move` (+ cop `_decide_move` for barriers); enhanced heuristic: belief
   argmax targeting, barrier-aware BFS distance (not raw Manhattan), cop barrier planning, thief
   evasion maximizing expected distance; LLM never chooses moves.
6. **Verbal layer** — hints capped at `hint_max_words` (15) with arena landmarks (`map_area`);
   providers: `template` (zero tokens, fallback), `ollama`, `claude_api` (Haiku, our default),
   `claude_cli`; `every_n_steps` throttling; token consumption metered and reported.
7. **GUI & Replay** — per-side Tkinter live GUI: local truth only (no bird's-eye view), belief
   heatmap (red intensity), turn banner (YOUR TURN / LOCKED); Replay Viewer loads a match log,
   steps forward/back, re-verifies every step's hash → green "Verified OK" or red "TAMPERED".
8. **Reliability layer** — Orchestrator as single gateway; state machine
   WAITING_FOR_OPPONENT→COMPUTING_MOVE→COMMITTING→AWAITING_REVEAL→VERIFYING (+TECHNICAL_LOSS);
   deadline on every MCP request (30 s default); watchdog (60 s freeze threshold) with state
   persistence and controlled shutdown.
9. **Reporting & league** — four lifecycle JSON files (declaration_<game_id>.json,
   config_<game_id>_g<NN>.json, log_<game_id>_g<NN>.json, result_<game_id>.json) with shared
   game_uid; Gmail API (scope gmail.send only) auto-report to rmisegal+uoh26finalgame@gmail.com as
   JSON attachment through Gatekeeper (quota manager + token bucket + DOS detector); game-count
   declaration; one counted game per opponent.

## 4. Non-Functional Requirements

- **Architecture:** SDK layer as single business entry point; no business logic in GUI/CLI; OOP,
  DRY, single responsibility; building-block design; every file ≤ 150 code lines.
- **Quality:** TDD (red-green-refactor); coverage ≥ 85% enforced; ruff clean (E,F,W,I,N,UP,B,C4,SIM);
  docstrings on every module/class/function; English-only code comments.
- **Configuration:** zero hardcoded values; JSON for shared/signed data, TOML for private per-peer
  data; overlay rule (shared JSON overrides private TOML); versioning from 1.00 everywhere.
- **Security:** no secrets in repo; `.env`/`credentials.json`/`token.json` git-ignored;
  `.env-example` committed; least-privilege OAuth scope.
- **Separation:** cop and thief run in two fully separate processes with separate config dirs
  (`config/police/`, `config/thief/`); no shared memory or live-state modules.
- **Tooling:** uv exclusively (pip/venv/python -m forbidden); pyproject.toml sole dependency
  source; uv.lock committed.
- **Performance/fairness:** heuristic strategy runs in milliseconds on a laptop; token budget
  ~200k per series, spendable down to zero via template fallback.

## 5. User Stories (selected)

- As the **cop agent**, I place a barrier next to the thief's suspected escape path so I can trap
  him within the step ceiling.
- As the **thief agent**, I detect that the cop's hint contradicts his scent field, lower my trust
  coefficient, and reroute my escape.
- As the **grader**, I clone the tagged repo, run `uv sync && uv run pytest`, load a match log in
  the Replay Viewer, and see **Verified OK** on every step.
- As the **team**, I get an automatic Gmail JSON report at game end without touching the keyboard.

## 6. Assumptions, Dependencies, Constraints, Out of Scope

- **Assumptions:** Python ≥3.10; opponent implements the same shared contract; both sides load a
  byte-identical `config/game.json` and refuse to play on mismatch.
- **Dependencies:** fastmcp, google-api-python-client + google-auth-oauthlib (Gmail),
  anthropic (Haiku verbal layer), tkinter (stdlib GUI), pytest/pytest-cov/ruff (dev), ngrok or
  Localtonet (external tunnel), GitHub, Moodle (submission).
- **Constraints:** all binding values come from the Mandatory Parameters Table (Appendix ו) via
  configuration — "minimum" values may only be raised by mutual agreement, "fixed" values never
  change; free natural language is the only inter-agent info channel about position (no numeric
  position protocol); LLM never makes movement decisions (absent documented mutual agreement).
- **Out of scope:** reinforcement learning (optional track not taken — documented decision);
  A2A/ACP protocols (recommended-only); playing more than `max_games_per_team` (10) league games.

## 7. Dedicated mechanism PRDs

| File | Mechanism | Dev priority (rulebook ch. 10) |
|---|---|---|
| docs/PRD_board_engine.md | Board, physics, scoring | Stage 1 |
| docs/PRD_p2p_mcp.md | FastMCP servers/clients, tunneling | Stages 2, 5 |
| docs/PRD_strategy.md | Brains, belief, decision policy | Stage 3 |
| docs/PRD_scent_language.md | Pheromones, hints, LLM providers | Stage 4 |
| docs/PRD_commit_reveal.md | Crypto, Step-0, audit | Stage 6 |
| docs/PRD_gui_replay.md | Live GUI, Replay Viewer | Stage 7 |
| docs/PRD_reporting_gatekeeper.md | Gmail API, Gatekeeper, lifecycle JSONs | Stage 7 |

## 8. Timeline and Milestones

Development follows the rulebook's seven-stage priority order (ch. 10), one PRD per stage, each
stage gated by an observed end-to-end milestone (see docs/TODO.md for the full task/commit plan):

1. **M1 Base logic:** two agents move legally on a 7×7 local board; barrier #15 rejected; overlap
   → capture. 2. **M2 MCP infra:** geometric message A→B over localhost decoded correctly.
3. **M3 Blind strategy:** known target → shortest path executed autonomously. 4. **M4 Language +
   scent:** free-language hint → inference; scent map updates/decays; hint produced (truth or lie).
5. **M5 Cloud:** remote peer over ngrok completes a full round. 6. **M6 Security:** commit→reveal
   with valid nonce verifies; Step-0 declaration signed. 7. **M7 Shell:** Gmail summary sent; GUI
   live; Replay App replays a recorded round. **M8 Submission:** compliance checklist (rulebook
   §11.5 + guidelines ch. 17) green; repo split (cop/thief); tag `v1.0-submission`.

## 9. Documented deviations / contradiction log

Per the rulebook's academic-freedom clause, contradictions found in the sources and our documented
choices are tracked in docs/PLAN.md §ADR. Current entries: board-size examples (7×7 vs 10×10 —
we follow Appendix ו: 7×7), axis convention (top-left origin, y grows downward — ch. 3 default),
commit-payload fields (rich canonical-JSON record per reference implementation).
