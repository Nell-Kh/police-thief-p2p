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
| 0.8 | Repo hygiene (ignore rules) + tidy up the task list | 2 | ✔ |
| 0.9 | **GATE: approve all documents before development starts** | — | ✔ |

## Phase 1 — Base logic (PRD_board_engine) → M1
| # | Task | Commits | Status |
|---|---|---|---|
| 1.1 | Config layer (config_io, schema, contract, ConfigManager) + constants + version + tests | 1 | ◐ |
| 1.2 | domain/board.py — grid, occupancy, barriers, bounds + tests | 1 | ☐ |
| 1.3 | domain/rules.py — move legality, no diagonals, barrier law, trap detection + tests | 1 | ☐ |
| 1.4 | domain/scoring.py — all termination events and point allocation + tests | 1 | ☐ |
| 1.5 | SDK skeleton + scripted single-process game → **M1 observed** | 1 | ☐ |

**M1:** two agents move legally on a 7×7 board; a barrier beyond the quota is rejected;
coordinate overlap triggers capture.

## Phase 2 — FastMCP infrastructure (PRD_p2p_mcp) → M2
| # | Task | Commits | Status |
|---|---|---|---|
| 2.1 | services/phase_machine.py — legal-transition table + tests | 1 | ☐ |
| 2.2 | services/deadline.py + watchdog.py + tests | 1 | ☐ |
| 2.3 | infra/mcp_server.py — exposed tools + tests | 1 | ☐ |
| 2.4 | infra/mcp_client.py — deadline-wrapped calls, retries + tests | 1 | ☐ |
| 2.5 | services/orchestrator.py + runtime, two processes → **M2 observed** | 1 | ☐ |

**M2:** a geometric message leaving the police peer over localhost is received and decoded
correctly at the thief peer.

## Phase 3 — Blind strategy (PRD_strategy) → M3
| # | Task | Commits | Status |
|---|---|---|---|
| 3.1 | domain/brain/base.py (BrainBase + class loader) + pathfind.py (barrier-aware BFS) + tests | 1 | ☐ |
| 3.2 | Blind police brain (pursue) + blind thief brain (evade) + tests | 1 | ☐ |
| 3.3 | Wire brains into PeerRuntime → **M3 observed** | 1 | ☐ |

**M3:** given a known target location, the agent computes and executes the shortest path with
no manual intervention.

## Phase 4 — Language + scent (PRD_scent_language) → M4
| # | Task | Commits | Status |
|---|---|---|---|
| 4.1 | domain/scent.py — 5×5 emission matrix, decay, clamp + tests | 1 | ☐ |
| 4.2 | domain/belief.py — Bayes update, barrier zeroing, normalization + tests | 1 | ☐ |
| 4.3 | domain/trust.py — lie detection (expected vs measured scent) + tests | 1 | ☐ |
| 4.4 | infra/llm/base.py + template.py (landmarks, 15-word cap) + tests | 1 | ☐ |
| 4.5 | infra/llm/claude_api.py + ollama.py + claude_cli.py + fallback chain + tests | 1 | ☐ |
| 4.6 | Enhanced brains: belief-driven pursuit, barrier planning, evasion + tests | 1 | ☐ |
| 4.7 | Token metering ledger → **M4 observed** | 1 | ☐ |

**M4:** a free-language report is translated into inference; the scent map updates and decays
every turn; the verbal layer produces a hint (truth or lie).

## Phase 5 — Cloud & tunneling → M5
| # | Task | Commits | Status |
|---|---|---|---|
| 5.1 | Public-URL support, tunnel docs, reconnect policy, timeout→TECHNICAL_LOSS + tests | 1 | ☐ |
| 5.2 | Remote round over a public tunnel → **M5 observed** | 1 | ☐ |

**M5:** an agent on a remote machine connects via the tunnel and plays a full round.

## Phase 6 — Security & crypto (PRD_commit_reveal) → M6
| # | Task | Commits | Status |
|---|---|---|---|
| 6.1 | domain/crypto.py — canonical JSON, SHA-256 commit/verify, nonces + tests | 1 | ☐ |
| 6.2 | domain/protocol.py — commit→ack→reveal→final-reveal flow + tests | 1 | ☐ |
| 6.3 | domain/step0.py — hardware declaration, github_commit, token cap, signing + tests | 1 | ☐ |
| 6.4 | domain/logbook.py — append-only match log, four lifecycle JSONs + tests | 1 | ☐ |
| 6.5 | domain/audit.py — mutual end-of-game audit, forgery → technical loss + tests | 1 | ☐ |
| 6.6 | domain/negotiation.py — config_sha256 + scent-model lock, game-count declaration → **M6** | 1 | ☐ |

**M6:** a move is committed then revealed with a valid nonce and verifies; Step-0 verifies
hardware and the commit hash.

## Phase 7 — Reporting & visualization shell → M7
| # | Task | Commits | Status |
|---|---|---|---|
| 7.1 | shared/bucket.py (token bucket) + gatekeeper.py (quota, DOS detector, FIFO queue) + tests | 1 | ☐ |
| 7.2 | infra/email/oauth.py (send-only scope) + sender.py (draft/send) + tests | 1 | ☐ |
| 7.3 | infra/email/reports.py — JSON attachment, result file assembly + tests | 1 | ☐ |
| 7.4 | gui/live.py + heatmap.py + banner.py — local truth only | 1 | ☐ |
| 7.5 | gui/replay.py — step fwd/back, per-step verification, Verified OK / TAMPERED | 1 | ☐ |
| 7.6 | End-to-end shell run → **M7 observed** | 1 | ☐ |

**M7:** a game summary is sent via Gmail; the GUI shows the live state; the Replay App replays
a recorded round with a valid verification stamp.

## Phase 8 — Research, compliance, submission → M8
| # | Task | Commits | Status |
|---|---|---|---|
| 8.1 | notebooks/analysis.ipynb — parameter research, sensitivity analysis, graphs | 1 | ☐ |
| 8.2 | Token cost analysis + budget table (guidelines ch. 11) | 1 | ☐ |
| 8.3 | docs/COMPLIANCE.md — rules #1–#55 + guidelines checklist → module/test map | 1 | ☐ |
| 8.4 | README.md full academic report (Dec-POMDP, dilemmas, strategies, screenshots) | 1 | ☐ |
| 8.5 | Verification pass: ruff 0, coverage ≥85%, 150-line audit, checklist §11.5; PROMPTS final | 1 | ☐ |
| 8.6 | Split into police-agent + thief-agent repos, cross-links, tag `v1.0-submission` | 1 | ☐ |

**M8:** both submission repos are tagged, cross-linked, and pass the full pre-submission
checklist.

---

**Definition of done (every task):** code ≤150 lines/file, docstrings on every module, class
and function, tests written with the code, ruff clean, coverage not below 85%, this file
updated, committed with a meaningful message.

