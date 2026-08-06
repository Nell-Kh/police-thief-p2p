# TODO — Task Tracking

**Project:** police-thief-p2p | **Version:** 1.00
**Owner:** the team — two members working jointly; individual task ownership is fluid,
so every row is owned by *team* and assignment happens in the daily sync, not in this file.

**Status key:** ☐ not started | ◐ in progress / in review | ✔ completed
**Priority key:** P0 blocking | P1 required for submission | P2 quality/polish

Work follows the rulebook's recommended development order (ch. 10). Every parent task is
expanded into the concrete sub-tasks that were actually performed inside it — the granular
record the guidelines' work-process chapter asks the tracker to preserve.

**Definition of done (applies to every task):** file stays within 150 lines of code,
docstrings on every module, class and function, tests written alongside the code,
`ruff check` clean, coverage not below 85%, this file updated, and the work committed
with a meaningful message.

---

## Phase 0 — Documentation & skeleton (guidelines ch. 2 mandatory work process)

| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 0.1 | **Repo skeleton** | P0 | team | ✔ |
| 0.1.1 | Initialize uv project with pyproject.toml and locked dependency set (uv.lock) | P0 | team | ✔ |
| 0.1.2 | Configure ruff: rule families E,F,W,I,N,UP,B,C4,SIM; line-length 100; target py310 | P0 | team | ✔ |
| 0.1.3 | Configure pytest + pytest-cov with the 85% fail_under gate wired into every run | P0 | team | ✔ |
| 0.1.4 | Write .gitignore covering .env, credentials.json, token.json, *.pem, *.key, caches | P0 | team | ✔ |
| 0.1.5 | Write .env-example documenting every environment variable without a single secret | P0 | team | ✔ |
| 0.1.6 | Set package layout src/police_thief with hatchling wheel target | P0 | team | ✔ |
| 0.1.7 | Verify empty-project gates: ruff clean, pytest collects, uv sync reproducible | P0 | team | ✔ |
| 0.2 | **Config skeleton** | P0 | team | ✔ |
| 0.2.1 | Author config/game.json mirroring every Appendix-F binding value verbatim | P0 | team | ✔ |
| 0.2.2 | Author per-peer TOMLs (police 8801, thief 8802) with [network], [strategy] sections | P0 | team | ✔ |
| 0.2.3 | Author config/rate_limits.json (gmail/anthropic/default service profiles) | P0 | team | ✔ |
| 0.2.4 | Author config/setup.json (GUI cell size) and logging_config.json | P0 | team | ✔ |
| 0.2.5 | Cross-check each numeric value against the rendered Appendix-F table page by page | P0 | team | ✔ |
| 0.2.6 | Decide overlay semantics: shared game.json values override private TOML keys | P0 | team | ✔ |
| 0.3 | **docs/PRD.md** | P0 | team | ✔ |
| 0.3.1 | Digest rulebook ch. 1-3 into product goals, actors and constraints | P0 | team | ✔ |
| 0.3.2 | Write functional requirements per subsystem with rule-number traceability | P0 | team | ✔ |
| 0.3.3 | Write non-functional requirements (150-line law, coverage, determinism) | P0 | team | ✔ |
| 0.3.4 | Define acceptance criteria per milestone M1-M8 | P0 | team | ✔ |
| 0.4 | **docs/PLAN.md** | P0 | team | ✔ |
| 0.4.1 | Draw C4 context and container views of the two-peer architecture | P0 | team | ✔ |
| 0.4.2 | Record ADR-1..ADR-6 (repo split, uv, strategy track, verbal-layer chain, transports, seal format) | P0 | team | ✔ |
| 0.4.3 | Define the data contracts: TurnMessage, sealed record, lifecycle files | P0 | team | ✔ |
| 0.4.4 | Map the seven mechanism PRDs to rulebook development-order stages | P0 | team | ✔ |
| 0.4.5 | Record and maintain ADR: one dev repo split at submission | P0 | team | ✔ |
| 0.4.6 | Record and maintain ADR: uv-only toolchain | P0 | team | ✔ |
| 0.4.7 | Record and maintain ADR: enhanced-heuristic strategy track | P0 | team | ✔ |
| 0.4.8 | Record and maintain ADR: verbal chain with template fallback | P0 | team | ✔ |
| 0.4.9 | Record and maintain ADR: transport abstraction | P0 | team | ✔ |
| 0.4.10 | Record and maintain ADR: seal format matches reference | P0 | team | ✔ |
| 0.4.11 | Record and maintain ADR: hidden-position wire (ADR-7) | P0 | team | ✔ |
| 0.4.12 | Record and maintain ADR: interop-kit conformance | P0 | team | ✔ |
| 0.5 | **docs/TODO.md** | P0 | team | ✔ |
| 0.5.1 | Encode the rulebook ch.10 development order as phases with milestones | P0 | team | ✔ |
| 0.5.2 | Define the standing definition-of-done applied to every task | P0 | team | ✔ |
| 0.5.3 | Set priority scheme P0/P1/P2 and status keys | P0 | team | ✔ |
| 0.6 | **Seven mechanism PRDs** | P0 | team | ✔ |
| 0.6.1 | PRD_board_engine: board, laws, scoring, engine, edge cases named | P0 | team | ✔ |
| 0.6.2 | PRD_p2p_mcp: tools, phases, deadline, watchdog, orchestrator seams | P0 | team | ✔ |
| 0.6.3 | PRD_strategy: BrainBase plug points, loader spec, blind then enhanced tracks | P0 | team | ✔ |
| 0.6.4 | PRD_scent_language: emission matrix, belief update, trust, verbal chain | P0 | team | ✔ |
| 0.6.5 | PRD_commit_reveal: seal construction, step-0, logbook, audit layers | P0 | team | ✔ |
| 0.6.6 | PRD_gui_replay: local-truth law, heatmap, replay verification stamps | P0 | team | ✔ |
| 0.6.7 | PRD_reporting_gatekeeper: three gates, lifecycle files, OAuth scope | P0 | team | ✔ |
| 0.7 | **README + docs/PROMPTS.md** | P1 | team | ✔ |
| 0.7.1 | Write the interim README (build, run, layout) pending the final academic report | P1 | team | ✔ |
| 0.7.2 | Open the prompts book with the digestion and scaffolding entries | P1 | team | ✔ |
| 0.7.3 | Adopt the entry template: context, prompt essence, output, lesson | P1 | team | ✔ |
| 0.7.4 | Write prompts-book entry 1 (source digestion) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.5 | Write prompts-book entry 2 (doc-first scaffolding) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.6 | Write prompts-book entry 3 (base logic) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.7 | Write prompts-book entry 4 (p2p layer) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.8 | Write prompts-book entry 5 (blind strategy) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.9 | Write prompts-book entry 6 (language+scent) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.10 | Write prompts-book entry 7 (cloud+tunneling) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.11 | Write prompts-book entry 8 (crypto core) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.12 | Write prompts-book entry 9 (networked loop) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.13 | Write prompts-book entry 10 (gatekeeper+gmail) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.14 | Write prompts-book entry 11 (region cop+concession) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.15 | Write prompts-book entry 12 (arms race) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.16 | Write prompts-book entry 13 (verbal duel) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.17 | Write prompts-book entry 14 (red team) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.18 | Write prompts-book entry 15 (wire fuzzing) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.19 | Write prompts-book entry 16 (speed-margin frontier) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.7.20 | Write prompts-book entry 17 (interop kit) with context/prompt/output/lesson | P1 | team | ✔ |
| 0.8 | **GATE: approve all documents before development starts** | P0 | team | ✔ |
| 0.8.1 | Review pass over all ten documents for internal consistency | P0 | team | ✔ |
| 0.8.2 | Confirm every config value traces to Appendix F | P0 | team | ✔ |
| 0.8.3 | Sign off the gate and record it before the first code commit | P0 | team | ✔ |

## Phase 1 — Base logic (PRD_board_engine) → M1

| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 1.1 | **Config layer** | P0 | team | ✔ |
| 1.1.1 | shared/config_io.py: read_json/read_toml with actionable ConfigError | P0 | team | ✔ |
| 1.1.2 | shared/config_io.py: canonical_json (sorted keys, compact separators, raw UTF-8) | P0 | team | ✔ |
| 1.1.3 | shared/config_io.py: sha256_of + apply_overlay (shared beats private) | P0 | team | ✔ |
| 1.1.4 | shared/schema.py: typed frozen dataclasses for every contract section | P0 | team | ✔ |
| 1.1.5 | shared/contract.py: raw dict -> GameContract builder with per-field errors | P0 | team | ✔ |
| 1.1.6 | shared/config.py: ConfigManager.load orchestrating both files per role | P0 | team | ✔ |
| 1.1.7 | constants.py: roles, MOVE_DELTAS (diagonals unrepresentable), phases, file names | P0 | team | ✔ |
| 1.1.8 | shared/version.py: single-source code version | P0 | team | ✔ |
| 1.1.9 | tests: config round-trips, overlay wins, missing-key errors, value pinning | P0 | team | ✔ |
| 1.2 | **domain/board.py** | P0 | team | ✔ |
| 1.2.1 | Square grid with in_bounds/is_free/neighbours/free_neighbours | P0 | team | ✔ |
| 1.2.2 | Irreversible barrier placement with BoardError on illegal cells | P0 | team | ✔ |
| 1.2.3 | tests: geometry, barrier permanence, off-board rejection | P0 | team | ✔ |
| 1.3 | **domain/rules.py** | P0 | team | ✔ |
| 1.3.1 | Move legality: orthogonal-only via destination/validate_move | P0 | team | ✔ |
| 1.3.2 | legal_moves/legal_steps in deterministic tie-break order | P0 | team | ✔ |
| 1.3.3 | Barrier law: stay-turn only, within one step, quota, free cell | P0 | team | ✔ |
| 1.3.4 | is_trapped: blocked cell or all exits blocked (rules 46/47) | P0 | team | ✔ |
| 1.3.5 | tests: 25 cases incl. corner traps, quota edge, diagonal rejection | P0 | team | ✔ |
| 1.4 | **domain/scoring.py** | P0 | team | ✔ |
| 1.4.1 | Outcome dataclass with points_for(role) | P0 | team | ✔ |
| 1.4.2 | capture/survival/technical_loss/tie constructors from ScoringConfig | P0 | team | ✔ |
| 1.4.3 | series_totals aggregation | P0 | team | ✔ |
| 1.4.4 | tests: every termination event against the Appendix-F table | P0 | team | ✔ |
| 1.5 | **SDK + scripted game → M1** | P0 | team | ✔ |
| 1.5.1 | domain/state.py: GameState ground truth + from_contract | P0 | team | ✔ |
| 1.5.2 | domain/engine.py: apply/end_turn with termination detection | P0 | team | ✔ |
| 1.5.3 | sdk/sdk.py: SimulationSdk facade for runners and tools | P0 | team | ✔ |
| 1.5.4 | CLI demo playing a scripted legal game end to end | P0 | team | ✔ |
| 1.5.5 | M1 observed: legal moves, quota rejection, overlap capture | P0 | team | ✔ |

## Phase 2 — FastMCP infrastructure (PRD_p2p_mcp) → M2

| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 2.1 | **services/phase_machine.py** | P0 | team | ✔ |
| 2.1.1 | Legal-transition table as data; transition() raising on anything else | P0 | team | ✔ |
| 2.1.2 | tests: every legal edge, every illegal edge refused | P0 | team | ✔ |
| 2.2 | **deadline.py + watchdog.py** | P0 | team | ✔ |
| 2.2.1 | DeadlineTracker with injected clock; expiry -> TECHNICAL_LOSS path | P0 | team | ✔ |
| 2.2.2 | Watchdog with beat/check, on_persist and on_shutdown callbacks | P0 | team | ✔ |
| 2.2.3 | tests: expiry, rescue, no real sleeps anywhere | P0 | team | ✔ |
| 2.3 | **infra/mcp_server.py** | P0 | team | ✔ |
| 2.3.1 | FastMCP server exposing the reference tool set | P0 | team | ✔ |
| 2.3.2 | Tool docs + payload forwarding to InboundHandler | P0 | team | ✔ |
| 2.3.3 | tests: registration, forwarding, documentation of every tool | P0 | team | ✔ |
| 2.4 | **infra/mcp_client.py** | P0 | team | ✔ |
| 2.4.1 | PeerClient with deadline-wrapped calls, retries and backoff from config | P0 | team | ✔ |
| 2.4.2 | Transport protocol + LoopbackTransport + FlakyTransport doubles | P0 | team | ✔ |
| 2.4.3 | tests: retry exhaustion, backoff sequence, unreachable -> technical loss | P0 | team | ✔ |
| 2.5 | **orchestrator + two processes → M2** | P0 | team | ✔ |
| 2.5.1 | Orchestrator as single entry point; wiring.py building subsystems | P0 | team | ✔ |
| 2.5.2 | recovery.py: crash rescue path preserving the logbook | P0 | team | ✔ |
| 2.5.3 | M2 observed: geometric message police -> thief over localhost decoded | P0 | team | ✔ |

## Phase 3 — Blind strategy (PRD_strategy) → M3

| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 3.1 | **brain/base.py + pathfind.py** | P0 | team | ✔ |
| 3.1.1 | BrainBase with _pick_move/_decide_move plug points | P0 | team | ✔ |
| 3.1.2 | load_brain: package.module:Class loader driven by TOML [strategy] | P0 | team | ✔ |
| 3.1.3 | pathfind: BFS distance_field, step_toward, step_away over live barriers | P0 | team | ✔ |
| 3.1.4 | tests: loader errors, field correctness, deterministic ties | P0 | team | ✔ |
| 3.2 | **Blind police + thief brains** | P0 | team | ✔ |
| 3.2.1 | BlindPoliceBrain: BFS pursuit + adjacent trap placement | P0 | team | ✔ |
| 3.2.2 | BlindThiefBrain: safety scoring with DEAD_END_PENALTY | P0 | team | ✔ |
| 3.2.3 | Rewrote unsatisfiable dead-end veto as bounded penalty (recorded lesson) | P0 | team | ✔ |
| 3.2.4 | tests: pursuit shortening, evasion lengthening, penalty firing | P0 | team | ✔ |
| 3.3 | **Wire brains into runtime → M3** | P0 | team | ✔ |
| 3.3.1 | services/runtime.py: configured_brain + LocalMatchRunner | P0 | team | ✔ |
| 3.3.2 | M3 observed: shortest-path execution with no manual intervention | P0 | team | ✔ |

## Phase 4 — Language + scent (PRD_scent_language) → M4

| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 4.1 | **domain/scent.py** | P0 | team | ✔ |
| 4.1.1 | Figure-4 emission with pre-series lock surface | P0 | team | ✔ |
| 4.1.2 | Verbatim update rule tau'=clamp((1-rho)tau+delta,0,0.9) | P0 | team | ✔ |
| 4.1.3 | expected_fresh_trail yardstick (0.81) | P0 | team | ✔ |
| 4.1.4 | tests: matrix digit-for-digit, decay curve, clamp both ends | P0 | team | ✔ |
| 4.2 | **domain/belief.py** | P0 | team | ✔ |
| 4.2.1 | BeliefMap: uniform prior, diffuse over legal motion model | P0 | team | ✔ |
| 4.2.2 | observe_scent multiplicative update + normalization off barriers | P0 | team | ✔ |
| 4.2.3 | observe_region hook + exclude negative evidence | P0 | team | ✔ |
| 4.2.4 | tests: convergence, barrier zeroing, degenerate renormalization | P0 | team | ✔ |
| 4.3 | **domain/trust.py** | P1 | team | ✔ |
| 4.3.1 | Hint parsing to cardinal directions; region_for halves/quadrants | P1 | team | ✔ |
| 4.3.2 | EWMA trust; corroborate/contradict verdicts vs the 0.81 yardstick | P1 | team | ✔ |
| 4.3.3 | tests: ch.4 worked example, liar erosion, landmark neutrality | P1 | team | ✔ |
| 4.4 | **infra/llm base + template** | P0 | team | ✔ |
| 4.4.1 | HintRequest/HintProvider contract with 15-word clip | P0 | team | ✔ |
| 4.4.2 | TemplateProvider: deterministic landmark hints per arena | P0 | team | ✔ |
| 4.4.3 | tests: word cap, determinism, direction wording, lie opposites | P0 | team | ✔ |
| 4.5 | **Paid providers + chain** | P1 | team | ✔ |
| 4.5.1 | claude_api (Haiku) with measured usage; ollama; claude_cli | P1 | team | ✔ |
| 4.5.2 | Chain: fallback(throttle(budget_guard(paid), template)) | P1 | team | ✔ |
| 4.5.3 | tests: no-key rescue, throttle routing, budget cutoff | P1 | team | ✔ |
| 4.6 | **Enhanced brains** | P1 | team | ✔ |
| 4.6.1 | EnhancedPoliceBrain: corridor pinch + barrier reserve | P1 | team | ✔ |
| 4.6.2 | EnhancedThiefBrain: trap-risk veto over blind safety | P1 | team | ✔ |
| 4.6.3 | tests: pinch fires, reserve held, veto prices adjacency | P1 | team | ✔ |
| 4.7 | **Token ledger → M4** | P1 | team | ✔ |
| 4.7.1 | TokenLedger: per-step and series totals against the 200k budget | P1 | team | ✔ |
| 4.7.2 | M4 observed: report -> inference; scent decays; hint truth or lie | P1 | team | ✔ |

## Phase 5 — Cloud & tunneling → M5

| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 5.1 | **Public-URL support** | P0 | team | ✔ |
| 5.1.1 | infra/http_transport.py: MCP-over-HTTP behind the Transport protocol | P0 | team | ✔ |
| 5.1.2 | services/peer_boot.py + peer CLI subcommand (serve + handshake) | P0 | team | ✔ |
| 5.1.3 | docs/TUNNELING.md: tunnel setup, reconnect policy | P0 | team | ✔ |
| 5.1.4 | Timeout path proven: dead opponent -> technical loss in 11s, no hang | P0 | team | ✔ |
| 5.2 | **Remote round → M5** | P0 | team | ✔ |
| 5.2.1 | Two real processes over HTTP: handshake observed OK | P0 | team | ✔ |
| 5.2.2 | M5 observed: full round over a public-style URL | P0 | team | ✔ |

## Phase 6 — Security & crypto (PRD_commit_reveal) → M6

| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 6.1 | **domain/crypto.py** | P0 | team | ✔ |
| 6.1.1 | new_nonce via secrets.token_hex(16); never random | P0 | team | ✔ |
| 6.1.2 | digest_of = sha256(canonical|nonce); seal/verify with compare_digest | P0 | team | ✔ |
| 6.1.3 | audit_records over a full disclosure | P0 | team | ✔ |
| 6.1.4 | tests: uniqueness, stability, smallest-change break, wrong nonce | P0 | team | ✔ |
| 6.2 | **Commit -> reveal flow** | P0 | team | ✔ |
| 6.2.1 | Wire carries commitment only; reveal deferred to audit (ADR-7) | P0 | team | ✔ |
| 6.2.2 | tests: cleartext position refused at the message layer | P0 | team | ✔ |
| 6.3 | **Step-0 record** | P0 | team | ✔ |
| 6.3.1 | sealing.step0_record: hardware spec, model, code_version, github_commit, budget | P0 | team | ✔ |
| 6.3.2 | shared/sysinfo.hardware_spec: os/machine/python/cpu/ram/gpu | P0 | team | ✔ |
| 6.3.3 | tests: mandatory fields, seal verifies, commit hash carried | P0 | team | ✔ |
| 6.4 | **domain/logbook.py** | P0 | team | ✔ |
| 6.4.1 | Append-only sealed records; commitments-only public view | P0 | team | ✔ |
| 6.4.2 | save/load as log_<game_id>_gNN.json with mandated name | P0 | team | ✔ |
| 6.4.3 | tests: append-only, name format, round-trip | P0 | team | ✔ |
| 6.5 | **domain/audit.py** | P0 | team | ✔ |
| 6.5.1 | Layer 1: re-hash every revealed record; one mismatch -> TAMPERED | P0 | team | ✔ |
| 6.5.2 | Layer 2: trajectory physics (start cell, displacement, barrier law) | P0 | team | ✔ |
| 6.5.3 | tests: clean pass, forged hash, hash-consistent teleport caught | P0 | team | ✔ |
| 6.6 | **domain/negotiation.py v1 → M6** | P0 | team | ✔ |
| 6.6.1 | Terms with contract digest, scent lock, game count, step0 commitment | P0 | team | ✔ |
| 6.6.2 | M6 observed: commit->reveal verifies; step-0 verified | P0 | team | ✔ |

## Phase 7 — Reporting & visualization shell → M7

| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 7.1 | **Networked turn loop (ADR-7)** | P0 | team | ✔ |
| 7.1.1 | Rewrote wire to negotiate/receive_turn/submit_audit tool set | P0 | team | ✔ |
| 7.1.2 | world_view.py: local truth + inference only, no opponent position field | P0 | team | ✔ |
| 7.1.3 | turn_taking.py: decide -> validate -> seal -> compose message | P0 | team | ✔ |
| 7.1.4 | turn_receiving.py: scent->belief, hint->trust, events, endings | P0 | team | ✔ |
| 7.1.5 | match_runtime.py: one peer's full mini-game engine | P0 | team | ✔ |
| 7.1.6 | Integration: full match, agreed verdict, mutual two-layer audit | P0 | team | ✔ |
| 7.2 | **bucket.py + gatekeeper.py** | P0 | team | ✔ |
| 7.2.1 | TokenBucket with verbatim tokens<-min(C,tokens+r*dt); injected clock | P0 | team | ✔ |
| 7.2.2 | Gatekeeper: daily quota, bucket, DOS lock; FIFO queue; monitoring log | P0 | team | ✔ |
| 7.2.3 | tests: refill math, gate order, lock, drain, overflow visibility | P0 | team | ✔ |
| 7.3 | **Gmail OAuth + sender** | P0 | team | ✔ |
| 7.3.1 | oauth.py: gmail.send single scope; token reuse/refresh/consent flow | P0 | team | ✔ |
| 7.3.2 | sender.py: MIME with JSON attachment; draft/send modes; 429 -> backoff | P0 | team | ✔ |
| 7.3.3 | configured_sender wiring recipient/mode/limits purely from config | P0 | team | ✔ |
| 7.3.4 | tests: all Google modules doubled; no network anywhere | P0 | team | ✔ |
| 7.4 | **reports.py lifecycle files** | P0 | team | ✔ |
| 7.4.1 | declaration/config/result payload builders sharing game_uid | P0 | team | ✔ |
| 7.4.2 | write_lifecycle_file in canonical bytes matching the mailed copy | P0 | team | ✔ |
| 7.4.3 | tests: sealed declaration verifies, totals recomputed, names derived | P0 | team | ✔ |
| 7.5 | **Live GUI** | P0 | team | ✔ |
| 7.5.1 | heatmap.py: belief reds, T? argmax, C self, barriers | P0 | team | ✔ |
| 7.5.2 | banner.py YOUR TURN/LOCKED; live.py window; coverage-excluded rendering | P0 | team | ✔ |
| 7.6 | **Replay viewer** | P0 | team | ✔ |
| 7.6.1 | replay.py: step fwd/back, per-step verify, Verified OK / TAMPERED | P0 | team | ✔ |
| 7.6.2 | tests: clean log verified, one edited byte voids the match | P0 | team | ✔ |
| 7.7 | **End-to-end shell → M7** | P0 | team | ✔ |
| 7.7.1 | scripts/m7_report_demo.py: play, write lifecycle files, gated send | P0 | team | ✔ |
| 7.7.2 | M7 observed with stub Gmail; real draft path documented for OAuth day | P0 | team | ✔ |

## Phase 8 — Research, strategy escalation, interop, compliance

| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 8.1 | **Research notebook** | P1 | team | ✔ |
| 8.1.1 | scripts/build_notebook.py: notebook authored as code, executed via nbclient | P1 | team | ✔ |
| 8.1.2 | Section 1: pinch sweep -> flat 0% capture surface | P1 | team | ✔ |
| 8.1.3 | Section 2: parity-dance diagnosis with distance trace | P1 | team | ✔ |
| 8.1.4 | Section 3-4: region cop + sensitivity sweep + crippled control | P1 | team | ✔ |
| 8.1.5 | Section 5-6: thief penalty sweep; exhaustive 1900-pair validation | P1 | team | ✔ |
| 8.1.6 | Every figure a real executed output; regeneration deterministic | P1 | team | ✔ |
| 8.1.7 | Author, execute and verify notebook section: pinch-sweep heatmap | P1 | team | ✔ |
| 8.1.8 | Author, execute and verify notebook section: parity-dance trace | P1 | team | ✔ |
| 8.1.9 | Author, execute and verify notebook section: region cop results | P1 | team | ✔ |
| 8.1.10 | Author, execute and verify notebook section: MIN_SHRINK×ENDGAME sensitivity + crippled control | P1 | team | ✔ |
| 8.1.11 | Author, execute and verify notebook section: thief first defense sweep | P1 | team | ✔ |
| 8.1.12 | Author, execute and verify notebook section: exhaustive 1900-pair validation | P1 | team | ✔ |
| 8.1.13 | Author, execute and verify notebook section: arms race round 1 (evader) | P1 | team | ✔ |
| 8.1.14 | Author, execute and verify notebook section: round 2 (wall cop) + histogram | P1 | team | ✔ |
| 8.1.15 | Author, execute and verify notebook section: red team + post-fix live check | P1 | team | ✔ |
| 8.1.16 | Author, execute and verify notebook section: belief transfer check over the wire | P1 | team | ✔ |
| 8.1.17 | Author, execute and verify notebook section: verbal duel table | P1 | team | ✔ |
| 8.1.18 | Author, execute and verify notebook section: token budget analysis | P1 | team | ✔ |
| 8.1.19 | Author, execute and verify notebook section: three-generation conclusions | P1 | team | ✔ |
| 8.2 | **Region cop** | P1 | team | ✔ |
| 8.2.1 | brain/region.py: safe-region minimization, exits tie-break, quota guards | P1 | team | ✔ |
| 8.2.2 | Fixed distance_field -1 semantics via _reach | P1 | team | ✔ |
| 8.2.3 | 1900/1900 captures, mean 7.8, max 11, ~2 stones | P1 | team | ✔ |
| 8.2.4 | tests: region math, endgame sealing, no-quota fallback | P1 | team | ✔ |
| 8.3 | **Concession protocol v1** | P0 | team | ✔ |
| 8.3.1 | Found: trapped thief went silent, winner never learned (first networked capture) | P0 | team | ✔ |
| 8.3.2 | concession_message sealed + auditable; on_turn returns the reply | P0 | team | ✔ |
| 8.3.3 | tests: emit once, sealed, cop accepts, wrong-side ignored | P0 | team | ✔ |
| 8.4 | **Arms race: evader + wall cop** | P1 | team | ✔ |
| 8.4.1 | Weight-blend search: lexicographic orders lose, blends win | P1 | team | ✔ |
| 8.4.2 | brain/evade.py: worst-case region + distance + openness + mobility (60/72 vs region cop) | P1 | team | ✔ |
| 8.4.3 | Minimax cop and anti-dance attempts recorded as failed designs | P1 | team | ✔ |
| 8.4.4 | brain/wall.py: center wall with guarded door, then region hunt | P1 | team | ✔ |
| 8.4.5 | Exhaustive: 1900/1900 vs every archetype, max 29/35, max 8/14 stones | P1 | team | ✔ |
| 8.4.6 | Notebook sections 7-8; regression tests pin the frontier | P1 | team | ✔ |
| 8.5 | **Verbal duel** | P1 | team | ✔ |
| 8.5.1 | Measured lie damage: 0.56 -> 2.69 belief error vs a hint-following cop | P1 | team | ✔ |
| 8.5.2 | Temporal TrustModel: scent-centroid displacement dot claimed direction | P1 | team | ✔ |
| 8.5.3 | DeceptionPolicy: honest/mislead/vague/adaptive off claim-gap feedback | P1 | team | ✔ |
| 8.5.4 | Vague style through template + Haiku prompts; 'right now' leak caught | P1 | team | ✔ |
| 8.5.5 | Result: lying at us (0.62) worse than silence (1.00); we poison naive cops | P1 | team | ✔ |
| 8.5.6 | Notebook section 10; config [deception] sections both peers | P1 | team | ✔ |
| 8.6 | **Red team** | P1 | team | ✔ |
| 8.6.1 | DoorCamper/SideFlipper/WallBlocker built against our own cop | P1 | team | ✔ |
| 8.6.2 | Pillar-orbit hole found (2/192): hunt stone became a merry-go-round | P1 | team | ✔ |
| 8.6.3 | Dance-breaker: repeated state buys an anchored hunt-preserving stone | P1 | team | ✔ |
| 8.6.4 | Re-validated exhaustively: six archetypes, 1900/1900, worst 32/35 | P1 | team | ✔ |
| 8.6.5 | Determinism redefined: fresh brain same state same decision | P1 | team | ✔ |
| 8.7 | **Wire hardening** | P0 | team | ✔ |
| 8.7.1 | services/enforcement.py: step continuity, scent physics, barrier law, claim permissions | P0 | team | ✔ |
| 8.7.2 | Type-safe TurnMessage.from_wire; NaN/inf/off-board scent refused | P0 | team | ✔ |
| 8.7.3 | Step-35 survival forgery closed by monotonicity | P0 | team | ✔ |
| 8.7.4 | 23-test hostile fuzz battery; violations land on the sender | P0 | team | ✔ |
| 8.8 | **Hybrid cop + claim pin** | P2 | team | ✔ |
| 8.8.1 | brain/hybrid.py: three commit tripwires; irreversible wall commitment | P2 | team | ✔ |
| 8.8.2 | Exhaustive truth: 1900/1900 vs weak at mean 12; 1891/1900 vs elite -> NOT default | P2 | team | ✔ |
| 8.8.3 | Verified-claim pin: cop scent corroborates claim -> thief belief pins (25x) | P2 | team | ✔ |
| 8.8.4 | Config documents both cop profiles with published numbers | P2 | team | ✔ |
| 8.9 | **Token cost analysis** | P2 | team | ✔ |
| 8.9.1 | Calls/tokens per mini-game and series; 14% budget utilization | P2 | team | ✔ |
| 8.9.2 | Parametric cost cell; fallback ladder bounds worst case at zero | P2 | team | ✔ |
| 8.10 | **Interop kit: vectors + conformance** | P0 | team | ✔ |
| 8.10.1 | Cloned class kit; read SPEC.md fully (1032 lines) | P0 | team | ✔ |
| 8.10.2 | Vendored MIT vectors into tests/vectors with license | P0 | team | ✔ |
| 8.10.3 | tests/interop/test_kit_vectors.py: 11 byte-exact conformance tests | P0 | team | ✔ |
| 8.10.4 | Fixed kernel IEEE drift: verbatim lookup replaces computed values | P0 | team | ✔ |
| 8.10.5 | Scent lock replaced by the registered multiplicative_book_v1 doc | P0 | team | ✔ |
| 8.10.6 | Vendor + conformance-check fixture `canonical_json` | P0 | team | ✔ |
| 8.10.7 | Vendor + conformance-check fixture `commit_reveal` | P0 | team | ✔ |
| 8.10.8 | Vendor + conformance-check fixture `delivery_contract` | P0 | team | ✔ |
| 8.10.9 | Vendor + conformance-check fixture `derive_starts` | P0 | team | ✔ |
| 8.10.10 | Vendor + conformance-check fixture `game_uid` | P0 | team | ✔ |
| 8.10.11 | Vendor + conformance-check fixture `joint_seed` | P0 | team | ✔ |
| 8.10.12 | Vendor + conformance-check fixture `locked_model` | P0 | team | ✔ |
| 8.10.13 | Vendor + conformance-check fixture `pairing_declaration` | P0 | team | ✔ |
| 8.10.14 | Vendor + conformance-check fixture `pheromone` | P0 | team | ✔ |
| 8.10.15 | Vendor + conformance-check fixture `report_consensus` | P0 | team | ✔ |
| 8.10.16 | Vendor + conformance-check fixture `scent_book_v3` | P0 | team | ✔ |
| 8.10.17 | Vendor + conformance-check fixture `smell_binding` | P0 | team | ✔ |
| 8.10.18 | Vendor + conformance-check fixture `terms_signature` | P0 | team | ✔ |
| 8.10.19 | Vendor + conformance-check fixture `uid_declaration` | P0 | team | ✔ |
| 8.11 | **Interop handshake** | P0 | team | ✔ |
| 8.11.1 | shared/interop.py: terms_from_contract (flat 14 keys), sign_terms, derive_game_ids | P0 | team | ✔ |
| 8.11.2 | negotiate_extras: pairing declaration + three locked-model hashes | P0 | team | ✔ |
| 8.11.3 | negotiation.py rewritten: value-equal terms, signature verify, truth-table refusals | P0 | team | ✔ |
| 8.11.4 | Omission-never-refuses honored both directions | P0 | team | ✔ |
| 8.11.5 | min_center_intensity plumbed through schema/contract/game.json | P0 | team | ✔ |
| 8.11.6 | InboundHandler + wiring + all fixtures migrated | P0 | team | ✔ |
| 8.12 | **At-least-once delivery (kit 7.1)** | P0 | team | ✔ |
| 8.12.1 | Dedupe on commit: same step+commit absorbed idempotently | P0 | team | ✔ |
| 8.12.2 | Same step different commit stays loud (equivocation) | P0 | team | ✔ |
| 8.12.3 | Duplicates never renew deadlines | P0 | team | ✔ |
| 8.12.4 | Conformance test over delivery_contract.json decision table | P0 | team | ✔ |
| 8.12.5 | Review resolved: accounting delivered; suite grew 580 → 588 | P0 | team | ✔ |
| 8.12.6 | Review resolved: capacity-2 reorder buffer + in-order replay, tested | P0 | team | ✔ |
| 8.13 | **Kit-shape capture final (kit 3.1)** | P0 | team | ✔ |
| 8.13.1 | Thief final: claim_response {claim:[own cell], caught:true} | P0 | team | ✔ |
| 8.13.2 | Zero-step final exemption in step law and dedupe | P0 | team | ✔ |
| 8.13.3 | Cop side: answer vs concession distinction; legacy win_claim tolerated | P0 | team | ✔ |
| 8.13.4 | Deferred to report alignment: audit-side concession corroboration (kit 3.1) | P0 | team | ☐ |
| 8.14 | **Report alignment (kit 6)** | P0 | team | ☐ |
| 8.14.1 | Consensus signature: spaced serialization, sign-then-insert Hebrew key | P0 | team | ☐ |
| 8.14.2 | mutual_agreement trimmed scope (game_id, aggregate, trimmed sub_games) | P0 | team | ☐ |
| 8.14.3 | Tie +2 added into total_score; diversity +10 never baked into totals | P0 | team | ☐ |
| 8.14.4 | League fields: games_played_including_this map with legal nulls; first_meeting; diversity flags | P0 | team | ☐ |
| 8.14.5 | Email = canonical bytes as body AND same file attached; recipient-gated arming | P0 | team | ☐ |
| 8.14.6 | Cross-check against kit examples/pairing-artifacts result file | P0 | team | ☐ |
| 8.15 | **Sparring series (kit)** | P0 | team | ☐ |
| 8.15.1 | Run kit verify_vectors.py locally on the Mac | P0 | team | ☐ |
| 8.15.2 | python -m sparring.cli selfplay: full six-sub-game series | P0 | team | ☐ |
| 8.15.3 | Fix every refusal the sparring peer explains until series is clean | P0 | team | ☐ |
| 8.15.4 | Both audits clean; artifacts joinable by game_id and game_uid | P0 | team | ☐ |
| 8.20 | **Belief-robust endgame (wire audit finding: cop converts only Blind over the wire)** | P0 | team | ☐ |
| 8.20.1 | Reproduce: wall cop vs Enhanced thief over the wire ends survival at 35 | P0 | team | ✔ |
| 8.20.2 | Recursive walls: quarter the thief's half, then corner it - position-free cuts | P0 | team | ☐ |
| 8.20.3 | Belief-mass region scoring: seal exits of the probable region, not the argmax | P1 | team | ☐ |
| 8.20.4 | Exploit claim answers: accumulated negative evidence in the confined half | P1 | team | ☐ |
| 8.20.5 | Wire-validation: cop converts Enhanced + Evade thieves over the real loop | P0 | team | ☐ |
| 8.16 | **docs/COMPLIANCE.md** | P1 | team | ✔ |
| 8.16.1 | Re-read Appendix E rules 1-55 verbatim from the rulebook | P1 | team | ✔ |
| 8.16.2 | Six rule groups mapped to module + proving test each | P1 | team | ✔ |
| 8.16.3 | Every cited test name verified to exist in the suite | P1 | team | ✔ |
| 8.16.4 | Guidelines checklist with live evidence; binding parameter table | P1 | team | ✔ |
| 8.16.5 | Trace rule #1 (two fully separate processes) to its module and proving test | P1 | team | ✔ |
| 8.16.6 | Trace rule #2 (no shared memory between sides) to its module and proving test | P1 | team | ✔ |
| 8.16.7 | Trace rule #3 (orchestrator sole entry point) to its module and proving test | P1 | team | ✔ |
| 8.16.8 | Trace rule #4 (formal state machine) to its module and proving test | P1 | team | ✔ |
| 8.16.9 | Trace rule #5 (illegal transitions rejected) to its module and proving test | P1 | team | ✔ |
| 8.16.10 | Trace rule #6 (deadline tracking vs freezes) to its module and proving test | P1 | team | ✔ |
| 8.16.11 | Trace rule #7 (watchdog + data rescue) to its module and proving test | P1 | team | ✔ |
| 8.16.12 | Trace rule #8 (live GUI local truth only) to its module and proving test | P1 | team | ✔ |
| 8.16.13 | Trace rule #9 (objective board never shown) to its module and proving test | P1 | team | ✔ |
| 8.16.14 | Trace rule #10 (tunnel to the public internet) to its module and proving test | P1 | team | ✔ |
| 8.16.15 | Trace rule #11 (byte-identical config both sides) to its module and proving test | P1 | team | ✔ |
| 8.16.16 | Trace rule #12 (minimums raised only by agreement) to its module and proving test | P1 | team | ✔ |
| 8.16.17 | Trace rule #13 (orthogonal movement only) to its module and proving test | P1 | team | ✔ |
| 8.16.18 | Trace rule #14 (diagonals rejected by the opponent) to its module and proving test | P1 | team | ✔ |
| 8.16.19 | Trace rule #15 (barriers declared openly) to its module and proving test | P1 | team | ✔ |
| 8.16.20 | Trace rule #16 (no lying about barrier location) to its module and proving test | P1 | team | ✔ |
| 8.16.21 | Trace rule #17 (SHA-256 commit-reveal) to its module and proving test | P1 | team | ✔ |
| 8.16.22 | Trace rule #18 (nonces secret until game end) to its module and proving test | P1 | team | ✔ |
| 8.16.23 | Trace rule #19 (hash mismatch = technical disqualification) to its module and proving test | P1 | team | ✔ |
| 8.16.24 | Trace rule #20 (replay viewer verifies the log) to its module and proving test | P1 | team | ✔ |
| 8.16.25 | Trace rule #21 (truth on capture) to its module and proving test | P1 | team | ✔ |
| 8.16.26 | Trace rule #22 (no false capture declarations) to its module and proving test | P1 | team | ✔ |
| 8.16.27 | Trace rule #23 (scent model locked pre-game) to its module and proving test | P1 | team | ✔ |
| 8.16.28 | Trace rule #24 (hardware declaration sealed) to its module and proving test | P1 | team | ✔ |
| 8.16.29 | Trace rule #25 (LLM never decides the move) to its module and proving test | P1 | team | ✔ |
| 8.16.30 | Trace rule #26 (free natural language only) to its module and proving test | P1 | team | ✔ |
| 8.16.31 | Trace rule #27 (no numeric-position protocol) to its module and proving test | P1 | team | ✔ |
| 8.16.32 | Trace rule #28 (token-bucket limiter for reports) to its module and proving test | P1 | team | ✔ |
| 8.16.33 | Trace rule #29 (DOS detector guards the account) to its module and proving test | P1 | team | ✔ |
| 8.16.34 | Trace rule #30 (gmail.send scope only) to its module and proving test | P1 | team | ✔ |
| 8.16.35 | Trace rule #31 (minimum counted games vs different teams) to its module and proving test | P1 | team | ✔ |
| 8.16.36 | Trace rule #32 (automatic Gmail reporting) to its module and proving test | P1 | team | ✔ |
| 8.16.37 | Trace rule #33 (report is standard JSON) to its module and proving test | P1 | team | ✔ |
| 8.16.38 | Trace rule #34 (never free-text reports) to its module and proving test | P1 | team | ✔ |
| 8.16.39 | Trace rule #35 (agreed result + two separate reports) to its module and proving test | P1 | team | ✔ |
| 8.16.40 | Trace rule #36 (mutual audit each game) to its module and proving test | P1 | team | ✔ |
| 8.16.41 | Trace rule #37 (exact games-count declaration) to its module and proving test | P1 | team | ✔ |
| 8.16.42 | Trace rule #38 (no false count declarations) to its module and proving test | P1 | team | ✔ |
| 8.16.43 | Trace rule #39 (no secrets in the repo ever) to its module and proving test | P1 | team | ✔ |
| 8.16.44 | Trace rule #40 (credentials in .gitignore) to its module and proving test | P1 | team | ✔ |
| 8.16.45 | Trace rule #41 (tagged submission version) to its module and proving test | P1 | team | ✔ |
| 8.16.46 | Trace rule #42 (comprehensive academic report) to its module and proving test | P1 | team | ✔ |
| 8.16.47 | Trace rule #43 (Moodle form saved as PDF untouched) to its module and proving test | P1 | team | ✔ |
| 8.16.48 | Trace rule #44 (individual Moodle submission per member) to its module and proving test | P1 | team | ✔ |
| 8.16.49 | Trace rule #45 (unique 8-char team code) to its module and proving test | P1 | team | ✔ |
| 8.16.50 | Trace rule #46 (barrier on thief's cell is capture) to its module and proving test | P1 | team | ✔ |
| 8.16.51 | Trace rule #47 (thief with no legal move is captured) to its module and proving test | P1 | team | ✔ |
| 8.16.52 | Trace rule #48 (score by the fixed table) to its module and proving test | P1 | team | ✔ |
| 8.16.53 | Trace rule #49 (two repos, cross-links, four JSON links) to its module and proving test | P1 | team | ✔ |
| 8.16.54 | Trace rule #50 (repo carries README/config/PRD/PLAN/TODO) to its module and proving test | P1 | team | ✔ |
| 8.16.55 | Trace rule #51 (reports to the binding agent address) to its module and proving test | P1 | team | ✔ |
| 8.16.56 | Trace rule #52 (one counted game per opponent) to its module and proving test | P1 | team | ✔ |
| 8.16.57 | Trace rule #53 (step-0 declares the commit hash) to its module and proving test | P1 | team | ✔ |
| 8.16.58 | Trace rule #54 (final JSON reports total tokens) to its module and proving test | P1 | team | ✔ |
| 8.16.59 | Trace rule #55 (self-grade code quality only) to its module and proving test | P1 | team | ✔ |
| 8.17 | **README.md academic report** | P0 | team | ☐ |
| 8.17.1 | Dec-POMDP formalism: states, observations, uncertainty | P0 | team | ☐ |
| 8.17.2 | FastMCP orchestration dilemmas: turns, failures, gatekeeper/orchestrator | P0 | team | ☐ |
| 8.17.3 | Strategy chapters: three generations with measured tables | P0 | team | ☐ |
| 8.17.4 | Verbal layer + deception findings; interop conformance section | P0 | team | ☐ |
| 8.17.5 | Screenshot slots: Live GUI belief map + Replay Verified OK (owner-supplied) | P0 | team | ☐ |
| 8.17.6 | Cross-repo link section; code-quality self-grade (rule 55) | P0 | team | ☐ |
| 8.17.7 | Abstract and system overview with the C4 view | P0 | team | ☐ |
| 8.17.8 | Dec-POMDP: state space, action space, observation model, reward | P0 | team | ☐ |
| 8.17.9 | Belief machinery: scent evidence, motion judge, negative evidence, claim pin | P0 | team | ☐ |
| 8.17.10 | Strategy generation 0-1: pinch failure and the region cop | P0 | team | ☐ |
| 8.17.11 | Strategy generation 2: wall cop, red team, hybrid frontier table | P0 | team | ☐ |
| 8.17.12 | Deception chapter: measured lie economics and the adaptive policy | P0 | team | ☐ |
| 8.17.13 | Orchestration dilemmas: turn-taking, failures, watchdog, gatekeeper | P0 | team | ☐ |
| 8.17.14 | Interop chapter: the kit, the vectors, the bytes we fixed | P0 | team | ☐ |
| 8.17.15 | Results tables reproduced from the notebook | P0 | team | ☐ |
| 8.17.16 | Limitations and future work | P0 | team | ☐ |
| 8.18 | **Verification pass** | P0 | team | ☐ |
| 8.18.1 | ruff clean, coverage >= 85%, 150-line audit across every file | P0 | team | ☐ |
| 8.18.2 | Guidelines section 11.5 checklist walked item by item | P0 | team | ☐ |
| 8.18.3 | Full suite + notebook regeneration from clean clone | P0 | team | ☐ |
| 8.18.4 | Audit every src file against the 150-code-line law (report the top five) | P0 | team | ☐ |
| 8.18.5 | Audit every test file against the 150-code-line law | P0 | team | ☐ |
| 8.18.6 | Docstring sweep: module, class, function coverage across src | P0 | team | ☐ |
| 8.18.7 | Hardcoded-value sweep: every literal traced to config or constants | P0 | team | ☐ |
| 8.18.8 | Secrets sweep: history and working tree | P0 | team | ☐ |
| 8.18.9 | Determinism sweep: replay two full matches byte-identically | P0 | team | ☐ |
| 8.18.10 | Re-run kit verify_vectors.py + our 11-test conformance suite | P0 | team | ☐ |
| 8.18.11 | Regenerate the notebook from scratch and diff committed outputs | P0 | team | ☐ |
| 8.18.12 | Fresh-clone build: uv sync, full suite, demo scripts on a clean machine | P0 | team | ☐ |
| 8.19 | **Repo split + tag** | P0 | team | ☐ |
| 8.19.1 | Create police-agent and thief-agent repos from the dev repo | P0 | team | ☐ |
| 8.19.2 | Per-repo configs, docs, cross-links in both READMEs | P0 | team | ☐ |
| 8.19.3 | Two Moodle links; four links in the result JSON | P0 | team | ☐ |
| 8.19.4 | Tag v1.0-submission in both; verify grader access | P0 | team | ☐ |
| 8.19.5 | Decide per-repo file partition (shared domain vs role-specific config) | P0 | team | ☐ |
| 8.19.6 | Scrub dev-only artifacts (.sync, scratch results) from both trees | P0 | team | ☐ |
| 8.19.7 | Author police-agent README with cross-link to thief-agent | P0 | team | ☐ |
| 8.19.8 | Author thief-agent README with cross-link to police-agent | P0 | team | ☐ |
| 8.19.9 | Verify both repos pass the full gates independently | P0 | team | ☐ |
| 8.19.10 | Grant grader access / set visibility per rule 49 | P0 | team | ☐ |
| 8.19.11 | Record both URLs into configs, step-0 and the result links block | P0 | team | ☐ |

## Phase 9 — League operations (human + agent, from the pairing playbook)

| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 9.1 | **Gmail OAuth day** | P0 | team | ☐ |
| 9.1.1 | Google Cloud project; enable Gmail API | P0 | team | ☐ |
| 9.1.2 | OAuth consent screen (External) + test users | P0 | team | ☐ |
| 9.1.3 | Scope restricted to gmail.send only | P0 | team | ☐ |
| 9.1.4 | Desktop-app OAuth client; download credentials.json into repo root (git-ignored) | P0 | team | ☐ |
| 9.1.5 | First authorization flow -> token.json minted | P0 | team | ☐ |
| 9.1.6 | Draft-mode rehearsal run; verify draft in mailbox | P0 | team | ☐ |
| 9.2 | **Identity** | P0 | team | ☐ |
| 9.2.1 | Choose the 8-character team code (no spaces) with partner | P0 | team | ☐ |
| 9.2.2 | Set group_name in both TOMLs; set real repo URLs | P0 | team | ☐ |
| 9.2.3 | Update step-0 group fields; re-run suite | P0 | team | ☐ |
| 9.3 | **Screenshots** | P0 | team | ☐ |
| 9.3.1 | Run live GUI during a self-play match; capture belief heatmap | P0 | team | ☐ |
| 9.3.2 | Run replay viewer on a saved log; capture Verified OK stamp | P0 | team | ☐ |
| 9.3.3 | Embed both into the README report section | P0 | team | ☐ |
| 9.4 | **Friendlies** | P0 | team | ☐ |
| 9.4.1 | Exchange first-contact message (turn order, model locks, ledger counts) | P0 | team | ☐ |
| 9.4.2 | Stage tunnels; handshake against a real opponent | P0 | team | ☐ |
| 9.4.3 | Play uncounted friendly; disarmed league fields verified | P0 | team | ☐ |
| 9.4.4 | Diff both sides' artifacts; fix any divergence | P0 | team | ☐ |
| 9.5 | **Counted series** | P0 | team | ☐ |
| 9.5.1 | Pre-T exchange of declared counts (rule 37) | P0 | team | ☐ |
| 9.5.2 | Counted six-sub-game series vs opponent one | P0 | team | ☐ |
| 9.5.3 | Counted series vs opponent two (min_games_to_pass=2) | P0 | team | ☐ |
| 9.5.4 | Both reports emailed; ledger advanced after each series | P0 | team | ☐ |

## Phase 10 — Test-suite inventory (every file, kept green under every refactor)

| # | Task | Priority | Owner | Status |
|---|---|---|---|---|
| 10.1 | Maintain `integration/test_blind_strategy.py` (7 tests) green under every refactor | P0 | team | ✔ |
| 10.2 | Maintain `integration/test_inference_loop.py` (4 tests) green under every refactor | P0 | team | ✔ |
| 10.3 | Maintain `integration/test_local_game.py` (13 tests) green under every refactor | P0 | team | ✔ |
| 10.4 | Maintain `integration/test_two_peers.py` (7 tests) green under every refactor | P0 | team | ✔ |
| 10.5 | Maintain `interop/test_kit_vectors.py` (13 tests) green under every refactor | P0 | team | ✔ |
| 10.6 | Maintain `unit/test_constants.py` (15 tests) green under every refactor | P0 | team | ✔ |
| 10.7 | Maintain `unit/test_domain/test_belief.py` (17 tests) green under every refactor | P0 | team | ✔ |
| 10.8 | Maintain `unit/test_domain/test_board.py` (18 tests) green under every refactor | P0 | team | ✔ |
| 10.9 | Maintain `unit/test_domain/test_brains.py` (16 tests) green under every refactor | P0 | team | ✔ |
| 10.10 | Maintain `unit/test_domain/test_crypto.py` (12 tests) green under every refactor | P0 | team | ✔ |
| 10.11 | Maintain `unit/test_domain/test_engine.py` (18 tests) green under every refactor | P0 | team | ✔ |
| 10.12 | Maintain `unit/test_domain/test_enhanced_brains.py` (9 tests) green under every refactor | P0 | team | ✔ |
| 10.13 | Maintain `unit/test_domain/test_hybrid_brain.py` (6 tests) green under every refactor | P0 | team | ✔ |
| 10.14 | Maintain `unit/test_domain/test_logbook_audit.py` (10 tests) green under every refactor | P0 | team | ✔ |
| 10.15 | Maintain `unit/test_domain/test_negotiation.py` (10 tests) green under every refactor | P0 | team | ✔ |
| 10.16 | Maintain `unit/test_domain/test_pathfind.py` (16 tests) green under every refactor | P0 | team | ✔ |
| 10.17 | Maintain `unit/test_domain/test_region_brain.py` (10 tests) green under every refactor | P0 | team | ✔ |
| 10.18 | Maintain `unit/test_domain/test_replay.py` (8 tests) green under every refactor | P0 | team | ✔ |
| 10.19 | Maintain `unit/test_domain/test_rules.py` (25 tests) green under every refactor | P0 | team | ✔ |
| 10.20 | Maintain `unit/test_domain/test_scent.py` (12 tests) green under every refactor | P0 | team | ✔ |
| 10.21 | Maintain `unit/test_domain/test_scoring.py` (13 tests) green under every refactor | P0 | team | ✔ |
| 10.22 | Maintain `unit/test_domain/test_sealing.py` (8 tests) green under every refactor | P0 | team | ✔ |
| 10.23 | Maintain `unit/test_domain/test_state.py` (13 tests) green under every refactor | P0 | team | ✔ |
| 10.24 | Maintain `unit/test_domain/test_trust.py` (18 tests) green under every refactor | P0 | team | ✔ |
| 10.25 | Maintain `unit/test_domain/test_turnmsg.py` (13 tests) green under every refactor | P0 | team | ✔ |
| 10.26 | Maintain `unit/test_domain/test_wall_and_evade.py` (11 tests) green under every refactor | P0 | team | ✔ |
| 10.27 | Maintain `unit/test_infra/test_email_oauth.py` (5 tests) green under every refactor | P0 | team | ✔ |
| 10.28 | Maintain `unit/test_infra/test_email_reports.py` (6 tests) green under every refactor | P0 | team | ✔ |
| 10.29 | Maintain `unit/test_infra/test_email_sender.py` (8 tests) green under every refactor | P0 | team | ✔ |
| 10.30 | Maintain `unit/test_infra/test_http_transport.py` (11 tests) green under every refactor | P0 | team | ✔ |
| 10.31 | Maintain `unit/test_infra/test_llm.py` (16 tests) green under every refactor | P0 | team | ✔ |
| 10.32 | Maintain `unit/test_infra/test_llm_providers.py` (10 tests) green under every refactor | P0 | team | ✔ |
| 10.33 | Maintain `unit/test_infra/test_mcp_client.py` (9 tests) green under every refactor | P0 | team | ✔ |
| 10.34 | Maintain `unit/test_infra/test_mcp_server.py` (4 tests) green under every refactor | P0 | team | ✔ |
| 10.35 | Maintain `unit/test_infra/test_transport.py` (5 tests) green under every refactor | P0 | team | ✔ |
| 10.36 | Maintain `unit/test_services/test_concession.py` (8 tests) green under every refactor | P0 | team | ✔ |
| 10.37 | Maintain `unit/test_services/test_deadline.py` (13 tests) green under every refactor | P0 | team | ✔ |
| 10.38 | Maintain `unit/test_services/test_deception.py` (9 tests) green under every refactor | P0 | team | ✔ |
| 10.39 | Maintain `unit/test_services/test_hostile_wire.py` (14 tests) green under every refactor | P0 | team | ✔ |
| 10.40 | Maintain `unit/test_services/test_inbound.py` (13 tests) green under every refactor | P0 | team | ✔ |
| 10.41 | Maintain `unit/test_services/test_orchestrator.py` (13 tests) green under every refactor | P0 | team | ✔ |
| 10.42 | Maintain `unit/test_services/test_phase_machine.py` (14 tests) green under every refactor | P0 | team | ✔ |
| 10.43 | Maintain `unit/test_services/test_watchdog.py` (9 tests) green under every refactor | P0 | team | ✔ |
| 10.44 | Maintain `unit/test_services/test_wiring.py` (4 tests) green under every refactor | P0 | team | ✔ |
| 10.45 | Maintain `unit/test_shared/test_bucket.py` (6 tests) green under every refactor | P0 | team | ✔ |
| 10.46 | Maintain `unit/test_shared/test_config.py` (15 tests) green under every refactor | P0 | team | ✔ |
| 10.47 | Maintain `unit/test_shared/test_config_io.py` (16 tests) green under every refactor | P0 | team | ✔ |
| 10.48 | Maintain `unit/test_shared/test_contract_values.py` (7 tests) green under every refactor | P0 | team | ✔ |
| 10.49 | Maintain `unit/test_shared/test_gatekeeper.py` (7 tests) green under every refactor | P0 | team | ✔ |
| 10.50 | Maintain `unit/test_shared/test_version.py` (11 tests) green under every refactor | P0 | team | ✔ |

## Test Accounting (delivery + capture-final work, from the 580 baseline to 588)
- `tests/interop/test_kit_vectors.py`: +3 (`test_delivery_contract_arrivals`, `test_no_reorder_window`, `test_buffered_steps_replay_in_order`)
- `tests/unit/test_services/test_concession.py`: +2 (`test_the_police_accepts_the_new_kit_shape_concession`, `test_a_claim_response_from_the_police_is_a_violation`)
- `tests/unit/test_services/test_inbound.py`: +2 (`test_a_concession_records_the_final_commit_without_overwriting`, `test_a_same_step_survival_claim_with_a_new_commit_is_refused`)
- `tests/unit/test_services/test_deadline.py`: +1 (`test_tolerated_traffic_never_renews_the_deadline`)

## Milestones

- **M1** two agents move legally on 7×7; quota-excess barrier rejected; overlap captures.
- **M2** a geometric message crosses localhost between the two peers and decodes.
- **M3** shortest-path pursuit executes with no manual intervention.
- **M4** free-language report → inference; scent decays; hints truth or lie.
- **M5** a remote agent connects via tunnel and plays a full round.
- **M6** commit→reveal verifies; Step-0 seals hardware and the commit hash.
- **M7** Gmail summary sent; live GUI shows local truth; replay stamps Verified OK.
- **M8** both submission repos tagged, cross-linked, checklist clean.
