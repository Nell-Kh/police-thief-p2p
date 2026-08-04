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

*(Entries continue as development proceeds.)*
