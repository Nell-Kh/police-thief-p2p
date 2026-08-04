# Prompts Book (ספר הפרומפטים) — AI-Assisted Development Log

Per guidelines §8.3: a log of all significant prompts used to build this project, their context,
goal, outputs, and iterative improvements. Maintained continuously; finalized at submission.

**Toolchain:** Claude (Cowork agent mode) orchestrating file tools, shell, subagents and tests.
The human (nell) directs, reviews and approves; the agent plans, generates and verifies.

---

## Entry 1 — Source-document digestion
- **Context:** project start; two governing PDFs (160-page rulebook, 39-page guidelines).
- **Prompt (essence):** "Read both PDFs completely and produce exhaustive digests: every
  mandatory rule vs recommendation, the full mandatory parameters table verbatim, all protocol
  details, formulas, schemas and checklists; verify tables/numbers against rendered PDF pages."
- **Output:** three digest documents (ch. 1-7; ch. 8-11+appendices; guidelines) used as the
  compliance source of truth for all subsequent work.
- **Lesson:** digesting the normative appendices (ה, ו) verbatim first prevents value drift in
  every later artifact — all config values trace to Appendix ו.

## Entry 2 — Documentation-first scaffolding
- **Context:** guidelines ch. 2 mandates PRD → PLAN → TODO → per-mechanism PRDs, approved before
  any code.
- **Prompt (essence):** "Scaffold the uv project (ruff/coverage gates per guidelines ch. 6-8),
  config skeleton mirroring the parameters table, then write PRD.md, PLAN.md (C4 + ADRs),
  TODO.md (~60-commit roadmap), and seven mechanism PRDs consistent with the master docs."
- **Output:** repo skeleton + 10 documents; ADRs recording the dev-repo-split decision, the
  enhanced-heuristic strategy track, and the claude_api-with-template-fallback verbal layer.
- **Lesson:** encoding the seven rulebook development priorities directly as PRD files + TODO
  phases keeps the commit history aligned with the mandated process.

## Entry 3 — Base logic, test-first
- **Context:** stage 1 of the rulebook's development order — the physical core, with no
  communication and no intelligence yet.
- **Prompt (essence):** "Build the board, the movement and barrier laws, the scoring table and
  the turn engine from PRD_board_engine. Every quantitative value must come from the signed
  contract, never from a literal in the code. Write the tests alongside, cover the edge cases
  named in the PRD (trapping placement, thief with no legal move, quota exhaustion, diagonal
  rejection), and keep every file within 150 lines."
- **Output:** `domain/board.py`, `rules.py`, `scoring.py`, `state.py`, `engine.py` plus the
  `SimulationSdk` facade and a CLI demo; 172 tests at 100% coverage.
- **Lesson:** naming the *edge cases* in the prompt is what produced them as tests. Asking for
  "tests" alone yields happy-path tests; asking for the specific boundary conditions from the
  PRD yields the ones that actually catch rule violations. Making illegal states unrepresentable
  helped too — because the move set is a fixed mapping, a diagonal move cannot be constructed at
  all rather than being validated away later.

## Entry 4 — The peer-to-peer layer
- **Context:** stage 2 of the development order — separate the two agents into independent
  processes and prove the pipe works before loading it with crypto or strategy.
- **Prompt (essence):** "Build the FastMCP peer layer from PRD_p2p_mcp: the tools a peer
  exposes, the client that calls them, the turn state machine with its exact transition table,
  the deadline tracker and the watchdog, and an Orchestrator that is the single gateway to all
  of them. Inject every clock and every transport so no test sleeps or touches the network."
- **Output:** `services/phase_machine.py`, `deadline.py`, `watchdog.py`, `inbound.py`,
  `orchestrator.py`, `wiring.py`, `recovery.py`; `infra/transport.py`, `mcp_client.py`,
  `mcp_server.py`; `domain/messages.py`. 289 tests, 99% coverage.
- **Lesson:** asking for *injected* clocks and transports up front was the highest-leverage
  instruction in the whole phase. It made every reliability path — retry, backoff, expired
  deadline, frozen loop — a fast deterministic test instead of something only observable
  against a real, misbehaving opponent. Two follow-up refactors also came out of a rule the
  prompt carried: splitting `wiring.py` and `recovery.py` out of the orchestrator to hold the
  150-line limit turned out to sharpen the responsibilities as well.

## Entry 5 — Blind strategy
- **Context:** stage 3 — a first decision core in a fully observable world, isolating the
  geometry from the uncertainty that arrives with scent and hints.
- **Prompt (essence):** "Implement BrainBase with the mandated `_pick_move`/`_decide_move`
  plug points and a `package.module:Class` loader driven by the TOML `[strategy]` section.
  Pursuit and evasion must use true BFS distances over the actual barriers, never raw
  Manhattan. Both brains deterministic; tie-breaks in the fixed move order."
- **Output:** `brain/base.py`, `pathfind.py`, `blind.py`, `services/runtime.py`; the CLI demo
  now runs the configured brains end to end. 328 tests, 99% coverage.
- **Lesson:** a test exposed that my first dead-end-avoidance rule could never fire (the veto
  condition was unsatisfiable on real geometry). Rewriting the rule as a bounded penalty inside
  one scoring function made it both simpler and testable — when a behavior is hard to write a
  test for, the behavior itself is usually mis-designed.

## Entry 6 — Language, scent and the competition brains (phase 4 complete)
- **Context:** stage 4 — the uncertainty layer, built after reading chapters 4-6 line by line
  and after resolving the reveal-vs-hidden-position contradiction against the lecturer's
  reference implementation (ADR-7).
- **Prompt (essence):** "Implement the printed emission matrix digit for digit with the
  pre-series SHA-256 lock; the reference-compatible belief update plus exclusion and a region
  hook; the 0.81-yardstick lie detector with an EWMA trust coefficient; four hint providers
  behind one interface with a token ledger, budget guard, step throttle and template fallback;
  and enhanced brains - corridor-pinching cop with a barrier reserve, trap-aware thief."
- **Output:** `domain/scent.py`, `belief.py`, `trust.py`, `brain/enhanced.py`,
  `infra/llm/` (base, ledger, template, chain, claude_api, ollama, claude_cli); M4 integration
  tests walking the full loop both truthfully and deceptively. 415 tests, 98% coverage.
- **Lesson:** two edges came from *reading the opponent*: the reference never parses hint text
  and discards negative capture-claim evidence — our trust layer and belief exclusion exploit
  exactly those gaps. And composing the paid providers as
  fallback(throttle(budget_guard(paid), template)) means the verbal layer can never cost a
  game: every guarantee is a wrapper, each testable alone.

## Entry 7 — Cloud and tunneling (phase 5)
- **Context:** stage 5 — from localhost to public addresses. The transport abstraction built in
  phase 2 pays off: a tunnel URL and a localhost port are the same code path.
- **Prompt (essence):** "Add the real MCP-over-HTTP transport behind the existing Transport
  protocol, a `peer` subcommand that boots one process per role (serve + handshake), tunnel
  documentation, and prove both directions live: a real two-process handshake over HTTP, and a
  dead opponent producing a clean technical loss instead of a hang."
- **Output:** `infra/http_transport.py`, `services/peer_boot.py`, the `peer` CLI subcommand,
  `docs/TUNNELING.md`. Observed live in two processes: handshake OK over HTTP; with the
  opponent down, three retries + backoff and a declared technical loss in 11 seconds.
- **Lesson:** because reliability was built into the client layer in phase 2, phase 5 needed no
  new failure handling at all — the tunnel is configuration, not code.

## Entry 8 — The cryptographic core (phase 6)
- **Context:** stage 6 — commit-reveal, sealed records, the mutual audit. Chapter 5 read line
  by line first; seal format matched to the league's de-facto reference implementation.
- **Prompt (essence):** "Seal sha256(canonical_json(payload) + '|' + nonce) with secrets-grade
  nonces; build the Step-0 record with the mandatory github_commit and the hardware spec; the
  per-turn sealed record with position/move/intent that never cross the wire; the turn message
  that REFUSES cleartext position fields; an append-only logbook saving log_<game_id>_gNN.json;
  terms negotiation locking contract digest + scent model + game-count declaration; and a
  TWO-layer audit - hashes, then trajectory physics."
- **Output:** `domain/crypto.py`, `sealing.py`, `turnmsg.py`, `logbook.py`, `audit.py`,
  `negotiation.py`, `shared/sysinfo.py`. 479 tests, 97.6% coverage.
- **Lesson:** the audit's physics layer is the phase's best idea and it came from auditing the
  *reference*: its audit checks hashes only, so a hash-consistent teleport passes. Ours fails
  it - the test seals a (2,3)->(6,6) "east" step with perfect hashes and the verdict is
  TAMPERED. Verifying what the adversary's verifier misses is worth points in a league where
  every opponent forked the same reference.

*(Entries continue as development proceeds.)*
