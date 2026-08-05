# COMPLIANCE — The Binding Rules, Mapped to Code and Tests

**Project:** police-thief-p2p | **Sources:** rulebook Appendix ה (rules #1–#55, quoted
category by category) and the software-engineering guidelines. Every rule below is mapped
to the module that implements it and the test that proves it. Status: ✔ implemented and
tested here | ⏱ performed at submission/league time (operational, not code).

The quantitative values behind these rules live in `config/game.json`, which mirrors the
binding parameter table of Appendix ו — see the table at the end.

---

## Group 1 — Network architecture, decentralization, local epistemology (rules #1–#10)

| # | Kind | Rule (essence) | Implementation | Proof | Status |
|---|---|---|---|---|---|
| 1 | must | Thief and cop run as two fully separate processes | Two peers, each `services/peer_boot.py` + own MCP server/port (8801/8802) | `test_two_peers.py` (two full runtimes, messages only); M2/M5 observed live | ✔ |
| 2 | never | No shared memory or variables between the sides | Only `TurnMessage` over MCP crosses; `WorldView` holds local truth exclusively | `test_two_peers.py` (full match over messages only) | ✔ |
| 3 | must | The orchestrator is the single entry point | `services/orchestrator.py` (+ `wiring.py`) | `test_orchestrator.py` | ✔ |
| 4 | must | Game states managed by a formal state machine | `services/phase_machine.py` | `test_phase_machine.py` | ✔ |
| 5 | must | Illegal state transitions are rejected | `PhaseMachine` raises on any transition outside its table | `test_phase_machine.py` | ✔ |
| 6 | must | Deadline tracking prevents freezes waiting for the opponent | `services/deadline.py`; timeout → TECHNICAL_LOSS | `test_deadline.py` | ✔ |
| 7 | must | A watchdog monitors process crashes and salvages data | `services/watchdog.py` + `recovery.py` | `test_watchdog.py` | ✔ |
| 8 | must | The live GUI shows local truth only | `gui/live.py` renders `WorldView` (belief argmax as "T?"), never the opponent's true cell | `gui/` design + rule #9 test | ✔ |
| 9 | never | The objective full board is never shown live | `WorldView` does not contain the opponent position at all — nothing to leak | `world_view.py` holds no opponent-position field at all; `test_turnmsg.py` refuses cleartext | ✔ |
| 10 | must | A tunnel exposes the local server publicly | `infra/http_transport.py` + `docs/TUNNELING.md` | `test_http_transport.py`; M5 observed | ✔ |

## Group 2 — Spatial mechanics, physics, board constraints (rules #11–#16)

| # | Kind | Rule (essence) | Implementation | Proof | Status |
|---|---|---|---|---|---|
| 11 | must | The config file is byte-identical on both sides | `shared/config_io.canonical_json` + sha256 compared at negotiation; mismatch → refusal | `test_negotiation.py::test_a_contract_mismatch_is_refused` | ✔ |
| 12 | must | Parameter minimums may only be raised by agreement, never lowered | `config/game.json` carries the Appendix-ו minimums; negotiation locks the shared hash | `test_contract_values.py` pins every binding value | ✔ |
| 13 | must | Movement is orthogonal only | `constants.MOVE_DELTAS` cannot express a diagonal; `rules.validate_move` | `test_rules.py` | ✔ |
| 14 | never | No diagonal moves — the opponent rejects them | `enforcement.py` + `rules.validate_move` applied to revealed moves in the audit physics layer | `test_rules.py::test_a_diagonal_or_unknown_move_is_rejected`; audit physics layer | ✔ |
| 15 | must | Every barrier placement is declared openly | `TurnMessage.barrier_placed` is a public event | `test_turnmsg.py`; `test_two_peers.py` | ✔ |
| 16 | never | Never lie about a barrier's location | Barrier goes into the sealed record AND the public message; audit cross-checks | `test_logbook_audit.py::test_a_teleport_fails_physics_even_with_clean_hashes` | ✔ |

## Group 3 — Cryptography, log integrity, zero-knowledge (rules #17–#24)

| # | Kind | Rule (essence) | Implementation | Proof | Status |
|---|---|---|---|---|---|
| 17 | must | SHA-256 commit-reveal protocol | `domain/crypto.py`: `sha256(canonical_json(payload) + "\|" + nonce)` | `test_crypto.py` | ✔ |
| 18 | must | Nonces stay secret until game end | `secrets.token_hex(16)`; nonces live only in the local logbook until disclosure | `test_crypto.py::test_nonces_never_repeat`; `turnmsg` refuses cleartext | ✔ |
| 19 | must | Any hash mismatch at audit = technical disqualification | `domain/audit.py` layer 1; one mismatch → TAMPERED, no discretion | `test_logbook_audit.py::test_a_forged_hash_is_tampered`; `test_replay.py` | ✔ |
| 20 | must | A replay viewer reconstructs and verifies the log | `domain/replay.py` + `gui/replay.py` (Verified OK / TAMPERED stamp) | `test_replay.py` | ✔ |
| 21 | must | Declare the truth when caught | `turn_taking._answer_claim` answers claims truthfully, always | `test_concession.py` | ✔ |
| 22 | never | No false capture declarations | The capture claim is the cop's own sealed position; a lie dies in the audit | `test_hostile_wire.py`; audit cross-check | ✔ |
| 23 | must | The scent-emission model is cryptographically locked pre-game | `negotiation.scent_lock_for` (sha256 of the emission matrix + decay) | `test_negotiation.py::test_a_scent_model_mismatch_is_refused` | ✔ |
| 24 | must | Cryptographic hardware declaration pre-game | `sealing.step0_record` + `shared/sysinfo.hardware_spec`, sealed as Step-0 | `test_sealing.py::test_step0_declares_the_mandatory_identity_fields` | ✔ |

## Group 4 — Strategy, language, public network (rules #25–#30)

| # | Kind | Rule (essence) | Implementation | Proof | Status |
|---|---|---|---|---|---|
| 25 | should | The LLM never decides the move; text only | Brains are pure Python; the provider composes hints only (`turn_taking`) | `test_llm.py`; brain tests are LLM-free | ✔ |
| 26 | must | Communication in free natural language only | Hints via `infra/llm/` providers, 15-word cap enforced | `test_llm.py` (word-cap tests) | ✔ |
| 27 | never | No direct numeric-position protocol | `TurnMessage.from_wire` REJECTS any message carrying `position`/`move`/`intent` | `test_turnmsg.py`; `test_hostile_wire.py` (cleartext = the cardinal sin) | ✔ |
| 28 | must | Token-bucket rate limiter for Gmail reports | `shared/bucket.py` (verbatim `tokens ← min(C, tokens + r·Δt)`) | `test_bucket.py` | ✔ |
| 29 | must | A DOS detector guards the network account | `shared/gatekeeper.py` (burst window → LOCKED, circuit breaker) | `test_gatekeeper.py` | ✔ |
| 30 | must | Gmail scope is send-only | `infra/email/oauth.py`: `GMAIL_SEND_SCOPE` is the single scope ever requested | `test_email_oauth.py` | ✔ |

## Group 5 — League fairness, administration, competitive integrity (rules #31–#45)

| # | Kind | Rule (essence) | Implementation | Proof | Status |
|---|---|---|---|---|---|
| 31 | must | Play the minimum counted games vs different teams | `min_games_to_pass` in `config/game.json`; scheduling is human | config pinned by `test_contract_values.py` | ⏱ league |
| 32 | must | Results reported automatically via Gmail | `infra/email/sender.py` through the Gatekeeper | `test_email_sender.py`; M7 demo | ✔ |
| 33 | must | The report is standard JSON | `infra/email/reports.py` canonical-JSON lifecycle files | `test_email_reports.py` | ✔ |
| 34 | never | Never a free-text report — JSON attachment only | `build_report_email` attaches `application/json`; body is a one-line note | `test_email_sender.py::test_the_report_is_a_machine_readable_json_attachment` | ✔ |
| 35 | must | Agree on the result; each team sends its own report | Mutual audit → agreed verdict; `result_payload` carries both SHA confirmations | `test_two_peers.py::test_a_full_match_reaches_an_agreed_verdict` | ✔ |
| 36 | must | Comprehensive mutual log audit at game end | `domain/audit.py` two layers: hashes + trajectory physics | `test_logbook_audit.py`; `test_two_peers.py::test_the_mutual_audit_passes_on_both_sides` | ✔ |
| 37 | must | Declare the exact counted-games number at match start | `negotiation.build_terms(games_played=…)`; `InboundHandler.opponent_games_played` | `test_negotiation.py`; `test_inbound.py` | ✔ |
| 38 | never | Never lie about the games count | Declaration goes into the signed terms; the lecturer's inbox is the oracle | terms are sealed — `test_negotiation.py` | ✔ |
| 39 | never | Never push secrets to the repo — even a private one | `.gitignore`: `.env`, `credentials.json`, `token.json`, `*.pem`, `*.key` | `.gitignore` in repo; no secret has ever been committed | ✔ |
| 40 | must | Credentials files are git-ignored | Same as #39 — both files listed explicitly | `.gitignore` lines 2–5 | ✔ |
| 41 | must | Tag the submission version in Git | `v1.0-submission` tag at the split (task 8.6) | ⏱ at submission | ⏱ |
| 42 | must | A comprehensive academic report in the repo | `README.md` full report (task 8.4: Dec-POMDP, dilemmas, strategies, screenshots) | ⏱ task 8.4 | ⏱ |
| 43 | must | Moodle form filled and saved as PDF, fields untouched | Human step at submission | — | ⏱ |
| 44 | must | Each team member submits individually on Moodle | Human step at submission | — | ⏱ |
| 45 | must | Unique 8-character team code, no spaces | `[game] group_name` in the private TOMLs (to be finalized before league play) | ⏱ set before first counted game | ⏱ |

## Group 6 — Completions found by cross-checking the book (rules #46–#55)

| # | Kind | Rule (essence) | Implementation | Proof | Status |
|---|---|---|---|---|---|
| 46 | must | A barrier on the thief's current cell is a capture | `rules.is_trapped` (cell blocked) → capture; `_apply_barrier` ends the thief's game | `test_rules.py`; `test_concession.py::test_a_trapping_barrier_makes_the_thief_concede` | ✔ |
| 47 | must | A thief with no legal move is captured | `rules.is_trapped` (all exits blocked) checked in `engine.end_turn` | `test_rules.py::test_an_agent_walled_in_on_all_four_sides_is_trapped` | ✔ |
| 48 | must | Score by the scoring table (capture 20/5, survival 5/10, technical 0/0) | `domain/scoring.py`, values from `config/game.json` | `test_scoring.py`; `test_contract_values.py` | ✔ |
| 49 | must | Two repos (cop, thief), cross-linked READMEs, 2 links on Moodle, 4 in the JSON | `reports.result_payload(repositories=…)` carries all four; split at task 8.6 | `test_email_reports.py` (four links asserted) | ✔/⏱ |
| 50 | must | Each repo contains README, config/, PRDs, PLAN, TODO at minimum | All present in `docs/` + `config/`; carried into both repos at the split | repo tree | ✔ |
| 51 | must | Reports go to the binding agent-report address | `constants.AGENT_REPORT_ADDRESS` = `rmisegal+uoh26finalgame@gmail.com`; recipient from config | `test_email_reports.py::test_the_binding_report_address` | ✔ |
| 52 | must | One counted game per opponent; warm-ups allowed | Declared via games-count terms (#37); scheduling is human | ⏱ league conduct | ⏱ |
| 53 | must | Step-0 declares the commit hash actually playing; update it each game | `step0_record(github_commit=…)` — mandatory argument, sealed | `test_sealing.py::test_step0_declares_the_mandatory_identity_fields` | ✔ |
| 54 | must | The final JSON reports total tokens consumed | `TokenLedger.total` → `result_payload(tokens_total=…)` | `test_llm.py` (ledger); `test_email_reports.py` | ✔ |
| 55 | must | Self-grade code quality only — never the league outcome | Self-assessment written for code quality in the README (task 8.4) | ⏱ task 8.4 | ⏱ |

---

## Software-engineering guidelines — the standing checklist

| Requirement | Where enforced | Evidence |
|---|---|---|
| Python managed with `uv` only (no pip/venv) | `pyproject.toml` + `uv.lock` | repo root |
| Every code file ≤ 150 lines | audited every commit | largest file: `orchestrator.py`, 131 code lines |
| Test coverage ≥ 85% | `pyproject.toml` `fail_under=85` — the suite FAILS below it | current: **97.9%**, 568 tests |
| `ruff check` clean (E,F,W,I,N,UP,B,C4,SIM; line 100) | `pyproject.toml` `[tool.ruff]` | `All checks passed!` |
| Docstring on every module, class and function | ruff D-adjacent review + convention | all modules |
| No hardcoded values — everything from configuration | `config/game.json` + per-peer TOMLs; `test_contract_values.py` pins them | ✔ |
| No secrets in the repository | `.gitignore` + rule #39/#40 | ✔ |
| PRD → PLAN → TODO before code; prompts book maintained | `docs/PRD*.md`, `PLAN.md`, `TODO.md`, `PROMPTS.md` (16 entries) | ✔ |
| Tests never depend on external services | Gmail/Anthropic/Google all mocked; fuzz battery is offline | `test_email_*`, `test_llm*` | 

## Binding parameter values (Appendix ו → `config/game.json`)

`grid_size=7`, `num_agents=2`, `max_barriers=14`, `max_moves=35`, `survival_threshold=35`,
scoring `20/5/5/10`, `tie=2`, `technical_loss=0`, `num_games=6` per series,
`diversity_reward=10`, `min_games_to_pass=2`, `max_games_per_team=10`,
`token_budget=200000` per series, `response_timeout=30s`, `watchdog=60s`,
`hint_max_words=15`, `map_area="New York"`, pheromone `center=0.9, decay=0.10`.
Every one of these is pinned by `tests/unit/test_shared/test_contract_values.py` — a
drifted value fails the suite, not the match.
