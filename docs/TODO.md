# TODO — Task Tracking and Commit Roadmap

**Project:** police-thief-p2p | **Version:** 1.00
Statuses: ☐ not started | ◐ in progress | ✔ completed. Each phase ends with an observed
end-to-end milestone (rulebook ch. 10).
Owner: nell (solo for now; partner may join — tasks are re-assignable).

---

## Phase 0 — Documentation & skeleton (guidelines ch. 2 mandatory work process)
| # | Task | Commits | Status |
|---|---|---|---|
| 0.1 | Repo skeleton: uv project, pyproject (ruff/coverage), .gitignore, .env-example | 1 | ✔ |
| 0.2 | Config skeleton: game.json (Appendix ו values), per-peer TOMLs, rate_limits, setup, logging | 1 | ✔ |
| 0.3 | docs/PRD.md | 1 | ✔ |
| 0.4 | docs/PLAN.md (C4, ADRs, contracts) | 1 | ✔ |
| 0.5 | docs/TODO.md (this file) | 1 | ✔ |
| 0.6 | 7 mechanism PRDs (PRD_board_engine … PRD_reporting_gatekeeper) | 2 | ✔ |
| 0.7 | README stub + docs/PROMPTS.md (prompts book, ongoing) | 1 | ✔ |
| 0.8 | **GATE: user approves all documents before development starts** | — | ☐ |

## Phase 1 — Base logic (PRD_board_engine) → M1
| # | Task | Commits | Status |
|---|---|---|---|
| 1.1 | shared/config.py (JSON+TOML load, overlay rule, versions) + tests | 1 | ☐ |
| 1.2 | constants.py + shared/version.py | 1 | ☐ |
| 1.3 | domain/board.py (grid, positions, barriers) + tests | 1 | ☐ |
| 1.4 | domain/rules.py (move legality, no diagonals, trap detection) + tests | 1 | ☐ |
| 1.5 | domain/scoring.py (all termination events) + tests | 1 | ☐ |
| 1.6 | sdk skeleton + local two-agent scripted game (single process demo) | 1 | ☐ |
| 1.7 | **M1 observed**: legal moves on 7×7; barrier > quota rejected; overlap→capture | 1 | ☐ |

## Phase 2 — FastMCP infrastructure (PRD_p2p_mcp) → M2
| # | Task | Commits | Status |
|---|---|---|---|
| 2.1 | infra/mcp_server.py (tools: handshake, receive_commit/reveal/hint, ack) + tests | 1 | ☐ |
| 2.2 | infra/mcp_client.py (deadline-wrapped calls, retries) + tests | 1 | ☐ |
| 2.3 | services/phase_machine.py (state machine) + tests | 1 | ☐ |
| 2.4 | services/deadline.py + services/watchdog.py + tests | 1 | ☐ |
| 2.5 | services/orchestrator.py + runtime skeleton (two processes, localhost) | 1 | ☐ |
| 2.6 | **M2 observed**: geometric message police→thief over localhost decoded | 1 | ☐ |

## Phase 3 — Blind strategy (PRD_strategy) → M3
| # | Task | Commits | Status |
|---|---|---|---|
| 3.1 | domain/brain/base.py (BrainBase, _pick_move, _decide_move) + loader from [strategy] | 1 | ☐ |
| 3.2 | domain/brain/pathfind.py (barrier-aware BFS distance field) + tests | 1 | ☐ |
| 3.3 | Blind police brain (chase known target) + blind thief brain (evade) + tests | 1 | ☐ |
| 3.4 | **M3 observed**: known target → shortest path executed autonomously | 1 | ☐ |

## Phase 4 — Language + scent (PRD_scent_language) → M4
| # | Task | Commits | Status |
|---|---|---|---|
| 4.1 | domain/scent.py (5×5 emission matrix, decay, clamp) + tests | 1 | ☐ |
| 4.2 | domain/belief.py (Bayes update, scent evidence, barrier zeroing) + tests | 1 | ☐ |
| 4.3 | domain/trust.py (lie detection: expected-vs-measured scent) + tests | 1 | ☐ |
| 4.4 | infra/llm/base.py + template.py (arena landmarks, 15-word cap) + tests | 1 | ☐ |
| 4.5 | infra/llm/claude_api.py (Haiku) + ollama.py + claude_cli.py + fallback chain + tests | 2 | ☐ |
| 4.6 | Enhanced brains: belief-driven police (incl. barrier planning) + thief + tests | 2 | ☐ |
| 4.7 | Token metering (consumption ledger) + tests | 1 | ☐ |
| 4.8 | **M4 observed**: hint→inference; scent updates+decays; hint (truth/lie) produced | 1 | ☐ |

## Phase 5 — Cloud & tunneling (PRD_p2p_mcp §5) → M5
| # | Task | Commits | Status |
|---|---|---|---|
| 5.1 | Public-URL support in config + client (ngrok/Localtonet docs & helpers) | 1 | ☐ |
| 5.2 | Resilience: reconnect policy, timeout→TECHNICAL_LOSS path + tests | 1 | ☐ |
| 5.3 | **M5 observed**: full round over a public tunnel URL | 1 | ☐ |

## Phase 6 — Security & crypto (PRD_commit_reveal) → M6
| # | Task | Commits | Status |
|---|---|---|---|
| 6.1 | domain/crypto.py (canonical JSON, SHA-256 commit/verify, nonces) + tests | 1 | ☐ |
| 6.2 | domain/protocol.py (commit→ack→reveal→final-reveal flow wiring) + tests | 1 | ☐ |
| 6.3 | domain/step0.py (hardware decl, github_commit, token cap, signing) + tests | 1 | ☐ |
| 6.4 | domain/logbook.py (append-only match log, four lifecycle JSONs) + tests | 1 | ☐ |
| 6.5 | domain/audit.py (mutual end-of-game audit, forgery→technical loss) + tests | 1 | ☐ |
| 6.6 | domain/negotiation.py (config exchange, config_sha256 lock, scent-model lock, game-count declaration) + tests | 1 | ☐ |
| 6.7 | **M6 observed**: commit→reveal verifies with valid nonce; Step-0 verified | 1 | ☐ |

## Phase 7 — Reporting & visualization shell (PRD_gui_replay, PRD_reporting_gatekeeper) → M7
| # | Task | Commits | Status |
|---|---|---|---|
| 7.1 | shared/bucket.py (token bucket) + gatekeeper.py (quota, DOS detector, queue) + tests | 2 | ☐ |
| 7.2 | infra/email/oauth.py (send-only scope) + sender.py (draft/send modes) + tests | 1 | ☐ |
| 7.3 | infra/email/reports.py (JSON attachment, result_<game_id>.json) + tests | 1 | ☐ |
| 7.4 | gui/live.py + heatmap.py + banner.py (local truth only) | 1 | ☐ |
| 7.5 | gui/replay.py (step fwd/back, per-step SHA-256 verify, Verified OK/TAMPERED) | 1 | ☐ |
| 7.6 | **M7 observed**: Gmail summary sent; GUI live; replay of a recorded round | 1 | ☐ |

## Phase 8 — Research, compliance, submission → M8
| # | Task | Commits | Status |
|---|---|---|---|
| 8.1 | notebooks/analysis.ipynb: parameter research (decay, board size, trust), graphs | 1 | ☐ |
| 8.2 | Token cost analysis + budget table (guidelines ch. 11) | 1 | ☐ |
| 8.3 | docs/COMPLIANCE.md: rules #1–#55 + guidelines checklist → module/test map | 1 | ☐ |
| 8.4 | README.md full academic report (Dec-POMDP, dilemmas, strategies, screenshots) | 2 | ☐ |
| 8.5 | docs/PROMPTS.md finalized (prompts book) | 1 | ☐ |
| 8.6 | Full verification: ruff 0, coverage ≥85%, 150-line audit, checklist §11.5 | 1 | ☐ |
| 8.7 | Split into police-agent + thief-agent repos, cross-links, per-repo READMEs | 2 | ☐ |
| 8.8 | Tag v1.0-submission on both repos; Moodle PDF + 8-char team code | — | ☐ |

**Definition of done (every task):** code ≤150 lines/file, docstrings, tests written with the
code, ruff clean, coverage not below 85%, TODO.md updated, committed with a meaningful message.

near 60+.
