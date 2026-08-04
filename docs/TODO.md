# TODO — Task Tracking

**Project:** police-thief-p2p | **Version:** 1.00
**Owner:** nell (solo for now; a partner may join — tasks are re-assignable).

**Status key:** ☐ not started | ◐ in progress | ✔ completed
**Priority key:** P0 blocking | P1 required for submission | P2 quality/polish

Work follows the rulebook's recommended development order (ch. 10): each phase is built,
tested and observed working end-to-end before the next one starts.

**Definition of done (applies to every task):** file stays within 150 lines of code,
docstrings on every module, class and function, tests written alongside the code, `ruff check`
clean, coverage not below 85%, this file updated, and the work committed with a meaningful
message.

---

## Phase 0 — Documentation & skeleton (guidelines ch. 2 mandatory work process)
| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 0.1 | Repo skeleton: uv project, pyproject (ruff/coverage), .gitignore, .env-example | P0 | nell | ✔ |
| 0.2 | Config skeleton: game.json (Appendix ו values), per-peer TOMLs, rate_limits, setup, logging | P0 | nell | ✔ |
| 0.3 | docs/PRD.md | P0 | nell | ✔ |
| 0.4 | docs/PLAN.md (C4 model, ADRs, data contracts) | P0 | nell | ✔ |
| 0.5 | docs/TODO.md (this file) | P0 | nell | ✔ |
| 0.6 | Seven mechanism PRDs (PRD_board_engine … PRD_reporting_gatekeeper) | P0 | nell | ✔ |
| 0.7 | README + docs/PROMPTS.md (prompts book, kept up to date) | P1 | nell | ✔ |
| 0.8 | **GATE: approve all documents before development starts** | P0 | nell | ✔ |

## Phase 1 — Base logic (PRD_board_engine) → M1
| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 1.1 | Config layer (config_io, schema, contract, ConfigManager) + constants + version | P0 | nell | ✔ |
| 1.2 | domain/board.py — grid, occupancy, barriers, bounds | P0 | nell | ✔ |
| 1.3 | domain/rules.py — move legality, no diagonals, barrier law, trap detection | P0 | nell | ✔ |
| 1.4 | domain/scoring.py — all termination events and point allocation | P0 | nell | ✔ |
| 1.5 | SDK skeleton + scripted single-process game → **M1 observed** | P0 | nell | ✔ |

**M1:** two agents move legally on a 7×7 board; a barrier beyond the quota is rejected;
coordinate overlap triggers capture.

## Phase 2 — FastMCP infrastructure (PRD_p2p_mcp) → M2
| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 2.1 | services/phase_machine.py — legal-transition table | P0 | nell | ✔ |
| 2.2 | services/deadline.py + watchdog.py | P0 | nell | ✔ |
| 2.3 | infra/mcp_server.py — exposed tools | P0 | nell | ✔ |
| 2.4 | infra/mcp_client.py — deadline-wrapped calls, retries | P0 | nell | ✔ |
| 2.5 | services/orchestrator.py + runtime, two processes → **M2 observed** | P0 | nell | ✔ |

**M2:** a geometric message leaving the police peer over localhost is received and decoded
correctly at the thief peer.

## Phase 3 — Blind strategy (PRD_strategy) → M3
| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 3.1 | domain/brain/base.py (BrainBase + class loader) + pathfind.py (barrier-aware BFS) | P0 | nell | ✔ |
| 3.2 | Blind police brain (pursue) + blind thief brain (evade) | P0 | nell | ✔ |
| 3.3 | Wire brains into PeerRuntime → **M3 observed** | P0 | nell | ✔ |

**M3:** given a known target location, the agent computes and executes the shortest path with
no manual intervention.

## Phase 4 — Language + scent (PRD_scent_language) → M4
| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 4.1 | domain/scent.py — 5×5 emission matrix, decay, clamp | P0 | nell | ✔ |
| 4.2 | domain/belief.py — Bayes update, barrier zeroing, normalization | P0 | nell | ✔ |
| 4.3 | domain/trust.py — lie detection (expected vs measured scent) | P1 | nell | ✔ |
| 4.4 | infra/llm/base.py + template.py (landmarks, 15-word cap) | P0 | nell | ✔ |
| 4.5 | infra/llm/claude_api.py + ollama.py + claude_cli.py + fallback chain | P1 | nell | ✔ |
| 4.6 | Enhanced brains: belief-driven pursuit, barrier planning, evasion | P1 | nell | ✔ |
| 4.7 | Token metering ledger → **M4 observed** | P1 | nell | ✔ |

**M4:** a free-language report is translated into inference; the scent map updates and decays
every turn; the verbal layer produces a hint (truth or lie).

## Phase 5 — Cloud & tunneling → M5
| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 5.1 | Public-URL support, tunnel docs, reconnect policy, timeout → TECHNICAL_LOSS | P0 | nell | ✔ |
| 5.2 | Remote round over a public tunnel → **M5 observed** | P0 | nell | ✔ |

**M5:** an agent on a remote machine connects via the tunnel and plays a full round.

## Phase 6 — Security & crypto (PRD_commit_reveal) → M6
| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 6.1 | domain/crypto.py — canonical JSON, SHA-256 commit/verify, nonces | P0 | nell | ✔ |
| 6.2 | domain/protocol.py — commit → ack → reveal → final-reveal flow | P0 | nell | ✔ |
| 6.3 | domain/step0.py — hardware declaration, github_commit, token cap, signing | P0 | nell | ✔ |
| 6.4 | domain/logbook.py — append-only match log, four lifecycle JSON files | P0 | nell | ✔ |
| 6.5 | domain/audit.py — mutual end-of-game audit, forgery → technical loss | P0 | nell | ✔ |
| 6.6 | domain/negotiation.py — config + scent-model lock, game-count declaration → **M6** | P0 | nell | ✔ |

**M6:** a move is committed then revealed with a valid nonce and verifies; Step-0 verifies
hardware and the commit hash.

## Phase 7 — Reporting & visualization shell → M7
| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 7.0 | Networked turn loop on the ADR-7 wire (negotiate/receive_turn/submit_audit tools) | P0 | nell | ✔ |
| 7.1 | shared/bucket.py (token bucket) + gatekeeper.py (quota, DOS detector, FIFO queue) | P0 | nell | ✔ |
| 7.2 | infra/email/oauth.py (send-only scope) + sender.py (draft/send) | P0 | nell | ✔ |
| 7.3 | infra/email/reports.py — JSON attachment, result file assembly | P0 | nell | ✔ |
| 7.4 | gui/live.py + heatmap.py + banner.py — local truth only | P0 | nell | ✔ |
| 7.5 | gui/replay.py — step forward/back, per-step verification, Verified OK / TAMPERED | P0 | nell | ✔ |
| 7.6 | End-to-end shell run (scripts/m7_report_demo.py) → **M7 observed** | P0 | nell | ✔ |

**M7:** a game summary is sent via Gmail; the GUI shows the live state; the Replay App replays
a recorded round with a valid verification stamp.

## Phase 8 — Research, compliance, submission → M8
| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 8.1 | notebooks/analysis.ipynb — parameter research, sensitivity analysis, graphs | P1 | nell | ✔ |
| 8.1b | Region cop (brain/region.py) — research outcome promoted to competition brain | P1 | nell | ✔ |
| 8.1c | Concession protocol — networked capture endings agree on both peers | P0 | nell | ✔ |
| 8.2 | Token cost analysis and budget table (guidelines ch. 11) | P2 | nell | ✔ |
| 8.3 | docs/COMPLIANCE.md — rules #1–#55 + guidelines checklist → module/test map | P1 | nell | ☐ |
| 8.4 | README.md full academic report (Dec-POMDP, dilemmas, strategies, screenshots) | P0 | nell | ☐ |
| 8.5 | Verification pass: ruff clean, coverage ≥85%, 150-line audit, checklist §11.5 | P0 | nell | ☐ |
| 8.6 | Split into police-agent + thief-agent repos, cross-links, tag `v1.0-submission` | P0 | nell | ☐ |

**M8:** both submission repos are tagged, cross-linked, and pass the full pre-submission
checklist.
