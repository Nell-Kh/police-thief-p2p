# PRD — Commit-Reveal Cryptographic Protocol, Step-0 and Mutual Audit

**Project:** police-thief-p2p | **Version:** 1.00 | **Status:** awaiting approval
**Parent docs:** docs/PRD.md §3.3, docs/PLAN.md §1.4/§3/§4 (ADR-1, ADR-6) | **Rulebook:** ch. 5, §3.4–3.5, §4.5, Appendix ה, Appendix ו
**Dev priority:** Stage 6 (rulebook ch. 10) — built only after P2P communication is proven.

---

## 1. Purpose & Theoretical Background

In a judge-less P2P game each side is both player and scribe of its own history, which invites
three fraud classes (rulebook §5.2): (1) *time travel* — altering a move already made; (2)
changing one's move after seeing the opponent's; (3) *denial* of a previous position or
declaration. The remedy is mathematical, not legal: the **Commit-Reveal** scheme ("coin flipping
by telephone"). A move is sealed in a SHA-256 hash before the opponent acts; changing it later
breaks the already-transmitted hash. The scheme embodies the spirit of zero-knowledge proof: at
commit time the opponent has absolute certainty *that a locked decision exists* and zero
knowledge of its content.

**The four mandatory cryptographic steps, in order, on every game step** (rulebook §5.3):

1. **Commit** — the agent picks its move, its hint, and an `intent` flag declaring in advance
   whether the hint is truth or a lie; draws a fresh nonce; serializes the full record as
   **canonical JSON** (sorted keys, fixed separators `(",", ":")`, UTF-8) and transmits **only**
   `H_commit = SHA256(canonical_record)`. The sealed record is the rich reference record:
   `{state, move, intent, hint, step, role, sub_game, nonce}` (ADR-6) — richer than the
   conceptual formula `SHA256(State ∥ Move ∥ Intent ∥ Nonce)`.
2. **Acknowledge** — the opponent confirms it received and is locked on the commitment; reveal
   happens only after both sides are locked.
3. **Reveal** — the agent discloses move + hint. **The nonce stays secret** to prevent premature
   reverse-engineering of past signatures (dictionary attack over the small move space).
4. **Final Reveal / Audit** — only at game end are **all** nonces disclosed, enabling full
   mutual re-hashing of every step of both logs.

Any recomputed hash that mismatches the committed hash **proves tampering unambiguously** —
SHA-256 flips on every bit — and yields a technical loss (grade 0, no appeal). Cryptography, not
human judgment, is the arbiter. Before move 1, a signed **Step-0** declaration fixes hardware,
LLM, code identity (`github_commit`) and the token budget, anchoring computational fairness.

## 2. Binding Parameters Used

| Parameter (Appendix ו) | Config key | Value | Status |
|---|---|---|---|
| Token estimate per series [אומדן טוקנים לסדרה] | `network_and_league.token_budget_per_series` | ~200000 | Negotiation |
| Number of mini-games [מספר המשחקונים] | `network_and_league.num_games` | 6 (series) | Fixed |
| Response time limit [מגבלת זמן התגובה] | `network_and_league.response_timeout_sec` | 30 s | Negotiation |
| Step ceiling [תקרת הצעדים] | `movement_and_barriers.max_moves` | 35 | Minimum |
| Scent focus / decay / field (locked model) | `pheromones.*` | 0.9 / 0.10 / 5×5 | Fixed |
| Technical loss score | `scoring.technical_loss` | 0 | Fixed |
| Log file name [קובץ היומן] | derived | `log_<game_id>_g<NN>.json` | Fixed naming |
| Declaration file [קובץ ההצהרה] | derived | `declaration_<game_id>.json` | Fixed naming |

Non-configurable protocol constants (code `constants.py`): nonce = `secrets.token_hex(16)`
(32 hex chars, 128 bits); hash = SHA-256 hex digest; canonical JSON separators; comparison via
`secrets.compare_digest`. These are protocol identity, not tunables.

## 3. Functional Requirements

- **FR-1 Canonical hashing (`domain/crypto.py`).** Serialize the commit record
  `{state, move, intent, hint, step, role, sub_game, nonce}` as canonical JSON
  (`sort_keys=True`, `separators=(",", ":")`, UTF-8) and return the SHA-256 hex digest. Both
  peers must hash byte-identical input for identical records.
- **FR-2 Nonce generation.** One fresh `secrets.token_hex(16)` per commitment. The `random`
  module is forbidden for any security value (predictable). A nonce is never reused.
- **FR-3 Commit step (`domain/protocol.py`).** Build the record, hash it, transmit **only**
  `H_commit` via the peer's MCP tool; retain the full record privately.
- **FR-4 Acknowledge step.** On receiving an opponent commitment, store `(step, role, h_commit)`
  append-only and return a positive ack; own reveal is blocked until the opponent's commit for
  the same step is acknowledged both ways.
- **FR-5 Reveal step.** Transmit `{state, move, intent, hint, step, role, sub_game}` — the
  record **minus the nonce**. Incoming reveals are stored next to the matching commitment;
  full verification is deferred to the final audit (the nonce is still missing by design).
- **FR-6 Final reveal.** At game end (capture, survival, or technical end) transmit the ordered
  list of all own nonces, keyed by step; receive the opponent's list.
- **FR-7 Mutual audit (`domain/audit.py`).** For every opponent step: recompose the record from
  the revealed fields + revealed nonce, recompute the hash (FR-1), compare with
  `secrets.compare_digest` to the hash acknowledged at commit time. Any mismatch ⇒ verdict
  `TAMPERED`, game result forced to technical loss (0 points, no appeal). All-match ⇒
  `VERIFIED_OK`. The same routine is exposed to the Replay Viewer (PRD_gui_replay.md).
- **FR-8 Intent sealing.** The truth/lie flag is part of the committed record, so an agent can
  never claim retroactively that it "lied on purpose"; the audit exposes intent history.
- **FR-9 Capture-claim truth duty.** On a cop Capture Claim the thief's answer is produced from
  its committed true position and logged signed; a false answer is arithmetically exposed at
  audit and treated as forgery (technical loss).
- **FR-10 Step-0 declaration (`domain/step0.py`).** Before the first move build, sign and
  exchange a JSON declaration: OS, CPU cores + frequency, RAM, GPU/VRAM presence, LLM name,
  code version, team name, mini-game number, **`github_commit`** (exact hash of the code being
  played — refreshed every game), and the agreed token budget. Token consumption is metered
  during play and cryptographically locked into the log so it cannot be denied. Persisted as
  `declaration_<game_id>.json`.
- **FR-11 Negotiation locks (`domain/negotiation.py`).** Pre-series: exchange `config/game.json`
  and refuse to play unless both `config_sha256` values (canonical-JSON hash) match
  byte-for-byte; exchange the full scent emission/decay model + numeric example and lock its
  SHA-256; exchange the game-count declaration (see PRD_reporting_gatekeeper.md).
- **FR-12 Logbook (`domain/logbook.py`).** Append-only per-step records (commit hash, ack,
  reveal, hint, verdicts, and — post-game — nonces) written to `log_<game_id>_g<NN>.json`,
  sharing `game_uid` with the other three lifecycle files.

## 4. Input/Output Contracts

```python
# domain/crypto.py
def canonical_json(record: dict) -> bytes                      # sorted keys, (",", ":"), UTF-8
def commit_hash(record: dict) -> str                           # SHA-256 hex of canonical_json
def make_nonce() -> str                                        # secrets.token_hex(16)
def verify_commit(record: dict, h_commit: str) -> bool         # secrets.compare_digest

# domain/protocol.py
@dataclass CommitRecord: state: str; move: str; intent: str; hint: str;
                         step: int; role: str; sub_game: int; nonce: str
def build_commit(rec: CommitRecord) -> tuple[str, CommitRecord]   # (h_commit, retained record)
def build_reveal(rec: CommitRecord) -> dict                       # record minus "nonce"
def build_final_reveal(records: list[CommitRecord]) -> dict[int, str]  # step -> nonce

# domain/step0.py
def collect_hardware() -> dict                                 # os, cpu, ram, gpu, llm, ...
def build_declaration(hw: dict, team: str, sub_game: int,
                      github_commit: str, token_budget: int) -> dict
def sign_declaration(decl: dict, key: bytes) -> str            # hash/HMAC over canonical JSON

# domain/audit.py
@dataclass StepVerdict: step: int; ok: bool; expected: str; recomputed: str
def verify_step(reveal: dict, nonce: str, h_commit: str) -> StepVerdict
def audit_log(opponent_log: list[dict], nonces: dict[int, str]) -> AuditReport
    # AuditReport.verdict in {"VERIFIED_OK", "TAMPERED"}; TAMPERED lists failing steps

# domain/negotiation.py
def config_sha256(shared_config: dict) -> str
def lock_scent_model(formula: str, numeric_example: dict) -> str
def negotiate(local_cfg: dict, remote_hash: str) -> bool       # False = refuse to play

# domain/logbook.py
class Logbook:                                                 # append-only; no mutation API
    def append(entry: dict) -> None
    def finalize(nonces: dict[int, str]) -> Path               # log_<game_id>_g<NN>.json
```

All functions are pure domain logic (no network/GUI I/O) so they are fully unit-testable;
transport happens in `infra/mcp_server.py` / `infra/mcp_client.py`.

## 5. Constraints & Mandatory-Rule References (Appendix ה)

- **#17** SHA-256 commit-and-reveal protocol is mandatory; its absence makes the solution illegal.
- **#18** Nonce absolutely secret until game end (dictionary-attack defense).
- **#19** Any hash mismatch at audit ⇒ technical disqualification, grade 0, no appeal.
- **#21 / #22** Truth-only answer to a Capture Claim; false capture declaration ⇒ grade 0.
- **#23** Scent emission/decay model cryptographically locked before the series.
- **#24 / #53** Signed Step-0 hardware declaration before the game; `github_commit` recorded and
  updated in every game (also mirrored in the end email JSON).
- **#54** Total tokens consumed reported in the end JSON — fed by the Step-0 token-budget lock
  and per-step metering.
- **#11 / #12** Byte-identical shared config on both sides; minimum values never lowered —
  enforced by the `config_sha256` negotiation gate.
- **#36** Comprehensive mutual log audit at every game end — precondition for agreeing the
  shared result JSON.
- **#15 / #16** Barrier placements are declared truthfully; they enter the committed record via
  `move`, so the audit also proves barrier honesty.
- Engineering: `secrets` only (never `random`); constant-time comparison; English-only comments;
  ≤ 150 code lines per file; coverage counts (no GUI here); zero hardcoded values.

## 6. Alternatives Considered & Justification

- **Minimal 4-field payload (`state‖move‖intent‖nonce`) vs. rich record** — the book's formula
  is conceptual; its reference implementation seals the richer record. We seal the rich record
  (ADR-6): stronger binding (hint and step cannot be retro-edited) and interop with the
  reference verifier. Chapter 7's `nonce|move` sketch is explicitly a simplification — rejected.
- **HMAC/asymmetric signatures instead of plain SHA-256 commitments** — rejected for the move
  protocol: the rulebook mandates SHA-256 commit-reveal (#17); public-key machinery adds key
  distribution without adding required security. A pre-supplied key signs only Step-0.
- **Per-step nonce reveal** (reveal nonce at Step 3) — rejected: violates #18 and enables
  incremental dictionary reconstruction of remaining commitments.
- **Mutable log with checksums** vs. **append-only logbook** — append-only chosen; mutation APIs
  would make accidental tampering possible and audit semantics ambiguous.

## 7. Success Criteria & Test Scenarios

- **T-1 Round-trip.** Given a full CommitRecord, when `commit_hash` then `verify_commit` with
  the same fields, then result is True; flipping any single field (even one hint character)
  yields False.
- **T-2 Canonical stability.** Given the same record with keys inserted in different orders,
  when hashed on "both peers", then digests are byte-identical.
- **T-3 Nonce quality.** Given 10 000 generated nonces, when compared, then all unique, 32 hex
  chars; static check: no `import random` in `domain/crypto.py`.
- **T-4 Order enforcement.** Given a peer that sends Reveal before Acknowledge completed, when
  the protocol handler runs, then the reveal is rejected and the state machine refuses the
  transition (services layer, rules #4/#5).
- **T-5 Nonce secrecy.** Given a mid-game reveal payload, when serialized, then it contains no
  `nonce` key (asserted structurally, not by string search only).
- **T-6 Forged log.** Given an opponent log where step 7's move was altered after commit, when
  `audit_log` runs with the revealed nonces, then verdict is TAMPERED, step 7 listed, and the
  game result is technical loss 0/0.
- **T-7 Clean audit.** Given two honest full logs (35 steps), when mutually audited, then
  verdict VERIFIED_OK and the shared result JSON can be produced.
- **T-8 Step-0 gate.** Given a game where the opponent's first commit arrives before Step-0
  declarations were exchanged, when the orchestrator dispatches it, then it is refused; given a
  declaration missing `github_commit`, then it is rejected as invalid.
- **T-9 Config lock.** Given local and remote `config/game.json` differing in one byte, when
  `negotiate` runs, then it returns False and no game starts (rule #11).
- **T-10 Edge — lie with intent=truth.** Given a committed record with `intent="truth"` and a
  hint later proven false against the audited positions, when audited, then the intent history
  is exposed in the audit report (data for the result agreement; scoring per rulebook).

## 8. File Split for the 150-Line Rule

Planned split (each file ≤ 150 code lines, PLAN §1.4): `domain/crypto.py` (hashing, nonces,
verify), `domain/protocol.py` (four-step flow records/builders), `domain/step0.py` (hardware +
declaration + signing), `domain/audit.py` (step verdicts + full audit), `domain/negotiation.py`
(config/scent/game-count locks), `domain/logbook.py` (append-only log + lifecycle file names).
If `protocol.py` outgrows the limit, split `protocol_records.py` (dataclasses) from
`protocol_flow.py` (builders); if `audit.py` outgrows it, split `audit_report.py`.

## 9. Out of Scope

- MCP transport, tunneling, retries and deadlines (PRD_p2p_mcp.md; services layer).
- Choosing the move/hint content (PRD_strategy.md, PRD_scent_language.md).
- Replay visualization of verification results (PRD_gui_replay.md — reuses `domain/audit.py`).
- Emailing lifecycle files and Gatekeeper protection (PRD_reporting_gatekeeper.md).
- Encrypting traffic in transit (not required; integrity, not confidentiality, is the goal).
