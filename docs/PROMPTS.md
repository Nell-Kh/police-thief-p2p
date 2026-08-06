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

## Entry 9 — The networked turn loop (phase 7, part 1)
- **Context:** migrating the wire to the ADR-7 protocol and making two complete runtimes play a
  real mini-game against each other, blind, over nothing but commitments, hints and scent.
- **Prompt (essence):** "Replace the legacy message set with negotiate/receive_turn/submit_audit;
  build WorldView (local truth + inference only - the opponent's position appears nowhere),
  turn_taking (brain decides, physics validated locally, record sealed, wire message built),
  turn_receiving (scent -> belief, hint -> trust, public events, endings), and MatchRuntime
  gluing them per role. Integration test: full match, agreed verdict, mutual two-layer audit."
- **Output:** rewritten `inbound.py`, `mcp_server.py`, `mcp_client.py`; new `world_view.py`,
  `turn_taking.py`, `turn_receiving.py`, `match_runtime.py`. 452 tests, 97.8% coverage.
- **Lesson:** the first full self-play match ended thief-survival 10-5 with the cop's final
  belief argmax EXACTLY on the thief's true cell - inference is solved, conversion is not: the
  cop knows where the thief is and still cannot corner it with only 4 barriers spent. The
  research notebook's tuning target is now obvious: proactive area-denial barriers, not
  reactive pinches.

## Entry 10 — Gatekeeper, Gmail OAuth and the lifecycle reports (phase 7, part 2)
- **Context:** rulebook ch. 9.3 + Appendix A, re-read line-by-line first. The iron rules
  extracted before coding: `gmail.send` scope ONLY; both secret files git-ignored; the report
  is a machine-readable JSON *attachment* (plaintext = rejected = points lost); HTTP 429 means
  back off, never blind-retry; each side mails its own report; four lifecycle files share one
  `game_uid`.
- **Prompt (essence):** "Build the token bucket with the book's verbatim update rule
  `tokens <- min(C, tokens + r*dt)`, the three-gate Gatekeeper (daily quota, bucket, DOS
  detector that LOCKS the pipe - sacrifice a report to save the account) with a FIFO overflow
  queue and a monitoring log; the Appendix-A OAuth flow with lazy Google imports so tests never
  touch the network; a sender with draft/send modes that turns 429 into the Gatekeeper's queue;
  and builders for declaration/config/result lifecycle files in canonical JSON, with the result
  totals recomputed from the per-mini-game rows so summary and detail can never disagree."
- **Output:** `shared/bucket.py`, `shared/gatekeeper.py`, `infra/email/{oauth,sender,reports}.py`,
  `scripts/m7_report_demo.py`. 495 tests, 98.0% coverage. **M7 observed**: a full mini-game →
  three lifecycle files on disk → the result report through all three gates → Gmail (stub here;
  a real Draft once `credentials.json` exists per Appendix A).
- **Lesson:** injecting the clock into both the bucket and the Gatekeeper made every rate/DOS
  test deterministic and instant - the first Gatekeeper test failed honestly (a 60-send burst
  tripped the DOS gate before the bucket could be observed), which is the pattern working
  exactly as ch. 9.3.1 warns: the gates are cumulative, and a test isolating one gate must
  deliberately open the others wide.

## Entry 11 — The research notebook, the region cop, and the concession (phase 8, part 1)
- **Context:** phase 8's parameter research, in a perfect-information harness (the cop is
  handed the thief's true cell - the ceiling of what belief can deliver).
- **Prompt (essence):** "Sweep the pinch cop's PINCH_RANGE × BARRIER_RESERVE over a grid of
  start pairs; diagnose the result; design whatever the diagnosis demands; validate
  exhaustively; add the ch. 11 token budget table; every figure must be the output of a real
  executed run."
- **Output:** `notebooks/analysis.ipynb` (regenerable via `scripts/build_notebook.py`),
  `domain/brain/region.py` (the new competition cop, selected in the TOML), the concession
  protocol (`turn_taking.concession_message`, receiver + runtime wiring), 511 tests, 97.8%
  coverage.
- **Lesson:** three, each earned the hard way. (1) The pinch cop's capture surface was flat
  **0%** across its whole parameter grid - a structural failure (the parity dance: equal
  speeds, orthogonal moves, a trap trigger that never fires on the diagonal), not a tuning
  miss; no sweep would have saved it. (2) The cure inverted the objective - stop minimizing
  distance to the thief, start minimizing the thief's *options* (its safe region, then its
  exit count): 1900/1900 captures, mean 7.8 steps, ~2 barriers of 14. (3) The first networked
  capture in the project's history immediately exposed a protocol hole nothing else could
  have found: the trapped thief knew it lost, went silent, and the winner never learned it
  won - fixed with a sealed, auditable concession message. A strategy improvement was also a
  protocol test.

## Entry 12 — The arms race: evader vs wall (phase 8, part 2)
- **Context:** the league grade rides on winning, so a 100%-vs-our-own-thief cop is not
  evidence of strength - it may be evidence of a weak thief. Both sides were forced to
  evolve against each other until neither could improve.
- **Prompt (essence):** "Make the thief beat the region cop, then make the cop beat that
  thief. No strict priority orderings without testing blends; every claim validated on the
  72-pair grid, finals on all 1900 pairs; pin the outcomes as regression tests."
- **Output:** `brain/evade.py` (EvadeThiefBrain - weighted blend of worst-case region,
  distance, openness, mobility: 60/72 survivals vs the region cop where the enhanced thief
  had 0), `brain/wall.py` (WallPoliceBrain - opening center wall with a guarded door, then
  the region hunt: 1900/1900 vs every archetype, max 29/35 steps, max 8/14 barriers), both
  wired as the configured competition brains; notebook sections 7-9; 524 tests, 97.8%.
- **Lesson:** four attempts died before the wall cop worked, and each death taught the
  design. Lexicographic thief scoring loses (blends win - defense is a trade-off, not a
  hierarchy). A minimax cop that assumes the thief's best reply never builds a wall (every
  stone looks futile one ply deep) and reverts to the parity dance. An anti-repetition
  trigger fires too rarely inside 35 steps. What finally won was changing the *board*, not
  the *chase*: the opening wall needs no position knowledge at all, which also makes it the
  one strategy immune to belief error - confirmed by an agreed capture verdict in full
  networked self-play.

## Entry 13 — The verbal duel: motion judge and adaptive deception (phase 8, part 3)
- **Context:** the hint is the game's only lying channel, and neither side of it had been
  stress-tested: what do systematic lies do to a cop's belief, and what should our own
  hints say?
- **Prompt (essence):** "Measure belief corruption per hint policy (honest/mislead/vague)
  against a naive cop and against our verifier; harden whatever the measurement breaks;
  make our own hint policy configurable and adaptive; every threshold justified by a
  number."
- **Output:** temporal `TrustModel` (scent-centroid displacement dotted with the claimed
  direction), `services/deception.py` (DeceptionPolicy: honest/mislead/vague/adaptive,
  driven by the opponent's own capture-claim distances), vague hint style through every
  provider (template pool + Haiku prompt), `[deception]` config sections; notebook section
  10; 533 tests, 97.8%.
- **Lesson:** three numbers carried the whole design. Lies inflated a hint-following cop's
  belief error 0.56 -> 2.69 cells - and fooled our own snapshot judge identically, because
  a walk north and its mirrored lie scent the same cells (a still image cannot verify a
  motion claim; two attempted static hardenings failed before this became obvious). The
  temporal judge flipped the sign: against it, lying (0.62) is now worse than silence
  (1.00) because every detected lie damps the falsely claimed region. And the funniest
  find: the test suite caught OUR OWN vague template leaking geometry - "right now"
  parses as east. The adversarial mindset applies to your own sentences too.

## Entry 14 — Red-teaming the wall cop (phase 8, part 4)
- **Context:** the wall cop's 1900/1900 was measured against thieves that don't know the
  wall exists - but league opponents can read our public repo. The only honest test is to
  attack our own agent with everything we would use against it.
- **Prompt (essence):** "Build thieves designed specifically to break the wall cop - camp
  the door, flip sides while the wall is open, park on the missing stones - and if any of
  them finds a hole, fix the cop and re-validate everything exhaustively."
- **Output:** the side flipper found a real hole (2/192 survivals). The trace was ironic:
  the cop's own hunt stone had become a *pillar*, and the thief orbited it in a 2-cycle -
  the parity dance reborn inside a pocket, where the region hunt's exit-sealing cannot
  reach. Fix: a repeated ``(cop, thief, stones)`` state now buys an anchored,
  hunt-preserving stone that cuts the orbit ring (in ``region.py``, so both cop brains
  inherit it). Re-validated exhaustively: all six archetypes fall 1900/1900, worst case 32
  of 35 steps, 10 of 14 stones. 535 tests, 97.7%.
- **Lesson:** validation breadth is not adversarial depth - no archetype in the zoo ever
  triggered the pillar orbit, because none of them had a reason to circle a stone; only a
  thief *designed against the wall* wandered into the one geometry that resurrects the
  dance. And the fix required instance memory, which quietly broke the determinism test -
  the right repair was to redefine determinism (fresh brain, same state, same decision),
  not to weaken the feature. Every strategy improvement is also a test-suite design
  question.

## Entry 15 — Fuzzing our own wire: the receive-side law (phase 8, part 5)
- **Context:** the last win-vector: hostile or buggy opponents. In a refereeless league of
  forked reference repos, garbage on the wire is a scoring event - caught, it voids the
  game as the sender's violation; uncaught, it crashes us and the watchdog charges US the
  technical loss.
- **Prompt (essence):** "Fuzz the real receive path with every hostile input class we can
  imagine - malformed types, step forgery, scent physics forgery (NaN/inf/over-cap/
  off-board), barrier quota and role abuse, claim spoofing - and make every one of them
  land as the opponent's technical loss, never as our exception."
- **Output:** ``services/enforcement.py`` (protocol_violation: step continuity, scent
  physics, barrier law, claim permissions - run before any inference), type-safe
  ``TurnMessage.from_wire``, opponent step/barrier counters in WorldView, a 23-test fuzz
  battery. 558 tests, 97.7%.
- **Lesson:** the nastiest holes were quiet, not loud. A thief could open with ``step=35``
  and an instant survival claim - nothing crashed, we simply lost; step monotonicity is
  what makes every other step-based check trustworthy. A single NaN scent value would
  have silently dissolved the whole belief map (NaN propagates through every multiply).
  And the fix immediately broke six of our own tests that sent step=5 out of nowhere -
  the enforcement layer could not tell our shortcuts from an attack, which is exactly
  the point.

## Entry 16 — The speed-margin frontier and the verified-claim pin (phase 8, part 6)
- **Context:** capture pays 20 points at step 9 or step 29, but every step is two more
  messages over a possibly-flaky tunnel - speed is operational safety. Could the cop have
  both the wall's guarantee and the hunt's speed?
- **Prompt (essence):** "Build a hybrid - hunt while the hunt works, commit to the wall
  the moment it stalls - and validate EXHAUSTIVELY, not on a sample grid. Separately: the
  cop's capture claims name its own cell; make the thief use that."
- **Output:** `brain/hybrid.py` (three commit tripwires: region stalled 2 turns / region
  still >14 at step 4 / step 12 deadline) as a documented, non-default config choice;
  the verified-claim belief pin in `turn_receiving.py` (a claim whose cell burns with
  the cop's own fresh scent in the same message pins the thief's cop-belief, factor 25;
  an unscented claim - a possible lie - moves nothing). 568 tests, 97.9%.
- **Lesson:** the 192-start grid said the hybrid was perfect (192/192 vs the elite
  evader); the exhaustive 1900-pair sweep found nine escapes the grid never sampled.
  Sample density is not proof - and the honest answer to a structural trade-off is not a
  cleverer threshold but a *configuration choice with published numbers*: the wall's
  guarantee ships as default, the hybrid's speed (mean ~12 vs ~25 steps, 1900/1900
  against reference-style thieves) is opt-in for opponents that have already shown a
  weak thief.

## Entry 17 — The league speaks: conforming to the class interop kit (phase 8, part 7)
- **Context:** classmates (imreeyal + anrbj666) published copthief-league-protocol - test
  vectors for every byte two implementations must agree on, plus a sparring peer. Their
  one-liner is the whole stake: two legal serializers that differ at all fail each other's
  audit, and BOTH score zero. The kit is also the de-facto handshake standard of every
  team we could play counted games against.
- **Prompt (essence):** "Vendor the vectors (MIT), run every one through OUR code, fix
  every byte that differs, and adopt the promoted handshake shape - flat signed terms,
  pairing declaration, locked-model hashes with the omission-never-refuses rule."
- **Output:** `shared/interop.py` (terms_from_contract, sign_terms, derive_game_ids, the
  three registered model declarations), negotiation + inbound rewritten to the greeting
  shape, `tests/interop/test_kit_vectors.py` (11 conformance tests, byte-exact),
  min_center_intensity plumbed through the contract. 580 tests, 97.9%.
- **Lesson:** the vectors caught a real bug within minutes: our scent kernel was COMPUTED
  (`0.9 * 42 / 90` = `0.42000000000000004`) instead of looked up verbatim (`0.42`) - one
  IEEE bit that would have put different bytes on the wire than the printed matrix. And
  our scent lock was exactly the "ad-hoc dict" the kit warns about: the same model as
  anrbj666's, guaranteed to refuse them for no reason. Interop is not a protocol problem,
  it is a bytes problem - and bytes are only provable with someone else's fixtures.

## Entry 18 — The unspoken ending (phase 8, part 8)
- **Context:** the wire audit showed our cop converting only the weakest thief over the
  real loop despite 1900/1900 in perfect information. The queued hypothesis was belief
  error in the endgame; the plan was recursive walls and belief-mass sealing.
- **Prompt (essence):** "Instrument the losing match step by step before designing
  anything: belief error, wall progress, stones, positions, every turn."
- **Output:** the trace acquitted the belief entirely - by step 28 the argmax was EXACT,
  both corner exits were sealed, and the thief was boxed in: rule 47, captured by the
  book's own law. But rule-47 endings are facts only the thief can observe, and our thief
  only spoke the rule-46 case (a barrier on its own cell); boxed in, it silently STAYed
  to a false survival. One conditional in MatchRuntime.on_turn (is_trapped -> kit-shape
  concession) closed it: Blind and Enhanced thieves now fall at step 28 over the wire
  with agreed verdicts. The kit's SPEC 3.1 warning described this exact fork, found live
  between two copies of their own sparring peer. 590 tests, 97.8%.
- **Lesson:** we almost built two sophisticated mechanisms (recursive walls, belief-mass
  sealing) to fix a problem that was one missing sentence on the wire. Instrument before
  designing: the cheapest diagnostic - printing the truth next to the belief every step -
  replaced a week of speculative strategy work with a five-line fix. And the fact that
  the kit documented this precise failure, from their own live fork, is the whole case
  for reading other people's postmortems as if they were your own.

*(Entries continue as development proceeds.)*
