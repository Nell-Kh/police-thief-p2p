# PRD — P2P FastMCP Layer, Reliability & Tunneling (Stages 2 + 5)

**Project:** police-thief-p2p | **Version:** 1.00 | **Status:** awaiting approval
**Parent documents:** docs/PRD.md §3.2/§3.8, docs/PLAN.md §1.3–§1.4, §2, ADR-1
**Rulebook source:** Chapters 2 and 8, Stage 5 of ch. 10 (+ Appendix ה rules #1–#7, #10)
**Target modules:** `src/police_thief/infra/mcp_server.py`, `infra/mcp_client.py`,
`services/orchestrator.py`, `services/phase_machine.py`, `services/deadline.py`,
`services/watchdog.py`, `services/runtime.py`

---

## 1. Purpose & Theoretical Background

This layer realizes the project's core architectural claim: a game with **no central
server, no referee, and no shared ground truth**. Each peer holds only its *local truth*
and verifies every opponent statement itself. The network is fully symmetric P2P: **every
peer is simultaneously an MCP server** (FastMCP, exposing tools via `@mcp.tool`) **and an
MCP client** of the opponent's server. The **MCP standard is a project requirement and may
not be replaced** (rulebook §2.3); A2A/ACP are recommended-only and not implemented.

Reliability is a first-class requirement, not an afterthought (rulebook ch. 8): the world —
network, model, opponent — is assumed to fail at the critical moment. The design applies
Separation of Concerns: an **Orchestrator** as the single gateway to five subsystems (MCP
connector, decision module, log manager, deadline tracker, watchdog); a strict
**state machine** as the first line of defense against deadlock; a **DeadlineTracker**
(timeout pattern) per request; and a **Watchdog** guarding the whole process. Each side
runs its *own* Orchestrator and state machine — the pattern is symmetric.

Development runs on localhost (Stage 2); league play **mandatorily** moves to public URLs
via a tunnel — ngrok or Localtonet (Stage 5, rule #10) — solving NAT traversal.

## 2. Binding Parameters Used

| Parameter (Appendix ו) | Config key | Value | Status |
|---|---|---|---|
| Response time limit | `network_and_league.response_timeout_sec` | 30 s | negotiation |
| Watchdog threshold | `network_and_league.watchdog_timeout_sec` | 60 s | negotiation |
| Number of mini-games per series | `network_and_league.num_games` | 6 (file default 1) | fixed (series = 6) |
| Retries / backoff | `rate_limiter_gatekeeper.max_retries` / `retry_backoff_sec` | 3 / 5 s | minimum |
| My port / opponent URL (private) | TOML `[network] my_port` / `opponent_url` | 8801/8802 dev | private per peer |

The ch. 8 example watchdog value (180 s) is illustrative only; the **binding** threshold is
Appendix ו's 60 s. "Negotiation" values default to the table value absent explicit agreement.

## 3. Functional Requirements

- **FR-1 Symmetric server.** `mcp_server.py` stands up one FastMCP instance per peer,
  exposing tools: `handshake` (identity, game-count declaration, config-hash exchange /
  negotiation), `receive_commit(h_commit, step, role)`, `ack(step)`,
  `receive_reveal(move, hint, intent_sealed, step)`, `receive_hint` (when hints travel
  separately), `capture_claim(step)`, `receive_barrier_decl(cell, step)`, and
  `audit_exchange(log_payload)` for the end-of-game nonce/log swap. Tool schemas are typed;
  every handler validates before accepting (never trust an unverified message).
- **FR-2 Symmetric client.** `mcp_client.py` wraps outbound calls to the opponent's URL
  (from private TOML) with the same tool vocabulary; every call carries a **deadline**.
- **FR-3 Absolute process separation.** Cop and thief run as **two fully separate
  processes** with separate config dirs `config/police/` vs `config/thief/`; **zero shared
  memory, zero shared live-state modules, zero shared variables** (rules #1, #2 —
  violation disqualifies the solution). Shared *code* (the installed package) is allowed;
  shared *state* is not. Enforced by design (no module-level mutable state) and by a test
  spawning both roles as subprocesses.
- **FR-4 Orchestrator as single gateway** (rule #3). `orchestrator.py` initializes MCP
  connections, wires the strategy brain, the log manager, DeadlineTracker and Watchdog;
  peripheral modules never reference each other — all coordination flows through it. It
  contains no decision logic and no low-level I/O itself.
- **FR-5 GamePhaseMachine** (rules #4, #5). Exact transition table (rulebook ch. 8, verbatim):

  | From | Legal targets |
  |---|---|
  | WAITING_FOR_OPPONENT | {COMPUTING_MOVE} |
  | COMPUTING_MOVE | {COMMITTING, TECHNICAL_LOSS} |
  | COMMITTING | {AWAITING_REVEAL} |
  | AWAITING_REVEAL | {VERIFYING, TECHNICAL_LOSS} |
  | VERIFYING | {WAITING_FOR_OPPONENT} |
  | TECHNICAL_LOSS | ∅ (terminal) |

  Any other transition raises immediately — a logic bug becomes a visible development-time
  error, never a silent in-match deadlock.
- **FR-6 DeadlineTracker** (rule #6). **Every MCP request carries a timestamp and an expiry
  deadline** (`response_timeout_sec`, 30 s default). A missed deadline is a **failure, not
  patience**: the tracker triggers a controlled retry (≤ `max_retries`, backoff
  `retry_backoff_sec`) and, on exhaustion, drives the phase machine to TECHNICAL_LOSS and
  closes the turn cleanly. No request is ever left hanging without an expiry.
- **FR-7 Watchdog** (rule #7). Independent background thread monitoring the main loop's
  **heartbeats**. If no heartbeat for `watchdog_timeout_sec` (60 s): **persist state**
  (game log + phase snapshot to disk for recovery/audit) and perform a **controlled
  shutdown** (release MCP connections, close logs) instead of a silent crash.
- **FR-8 PeerRuntime.** `runtime.py` runs the negotiation → turn loop → audit lifecycle of
  one peer, emitting heartbeats, calling the strategy module at the mandated point
  (after hint-decode, before commit-pack), and translating phase-machine state to the GUI
  turn banner. It is the only place the turn sequence (PLAN §3) is encoded.
- **FR-9 Tunneling** (rule #10). Localhost is allowed **only during early development**;
  for the league every peer **must** be exposed via a public tunnel URL (ngrok or
  Localtonet). The runtime takes the public URL from config, logs it into the declaration
  file, and refuses "league mode" on a localhost opponent URL. Tunnel drop mid-game is a
  deadline failure path, not a hang (a fallen tunnel must not deadlock turn scheduling).
- **FR-10 Handshake refusal.** Before mini-game 1 the peers exchange `config_sha256` of the
  shared `config/game.json`; **any mismatch refuses play** (rule #11 dependency).

## 4. Input/Output Contracts

```python
# infra/mcp_server.py — inbound tool surface (FastMCP)
@mcp.tool def handshake(payload: HandshakeIn) -> HandshakeOut
    # HandshakeIn: {team_id: str, games_played: int, config_sha256: str, public_url: str}
@mcp.tool def receive_commit(h_commit: str, step: int, role: str) -> AckOut   # {accepted: bool}
@mcp.tool def ack(step: int) -> AckOut
@mcp.tool def receive_reveal(move: str, hint: str, step: int) -> RevealOut
    # RevealOut: {verified_pending: bool}  (hash check happens locally, then VERIFYING)
@mcp.tool def receive_barrier_decl(cell: list[int], step: int) -> AckOut
@mcp.tool def capture_claim(step: int) -> ClaimOut     # {answer: "confirm"|"deny", signed: str}
@mcp.tool def audit_exchange(log_json: str) -> AuditOut  # {verified: bool, mismatches: list}

# infra/mcp_client.py
class PeerClient:
    def __init__(self, opponent_url: str, deadlines: DeadlineTracker): ...
    async def call(self, tool: str, payload: dict, deadline_sec: float | None = None) -> dict
        """Raises DeadlineExpired after retries; never blocks unboundedly."""

# services/phase_machine.py
class GamePhaseMachine:
    TRANSITIONS: dict[str, set[str]]        # exactly the table in FR-5
    state: str                              # starts WAITING_FOR_OPPONENT
    def transition(self, target: str) -> str  # raises IllegalTransitionError

# services/deadline.py
class DeadlineTracker:
    def track(self, request_id: str, timeout_sec: float) -> Deadline
    def expired(self) -> list[Deadline]
class Deadline: request_id: str; sent_at: float; expires_at: float

# services/watchdog.py
class Watchdog:
    def __init__(self, timeout_sec: float, persist: Callable[[], None],
                 shutdown: Callable[[], None]): ...
    def beat(self) -> None                  # called by the main loop each iteration
    def check(self) -> Literal["ALIVE", "SHUTDOWN"]

# services/orchestrator.py / runtime.py
class Orchestrator:
    def __init__(self, cfg: PeerConfig): ... # wires server, client, brain, log, deadline, watchdog
    def run(self) -> GameResult
class PeerRuntime:
    def play_turn(self) -> TurnRecord        # one full phase-machine cycle
    def run_series(self) -> SeriesResult
```

## 5. Constraints & Mandatory-Rule References

- Appendix ה **#1/#2** — two separate processes; no shared memory/variables (disqualification).
- **#3** — Orchestrator as single entry point; **#4/#5** — proper state machine, every
  illegal transition rejected; **#6** — deadline tracking on every wait; **#7** — watchdog
  with controlled data rescue; **#10** — tunneling for league play.
- Rulebook §2.3 — **MCP must not be replaced**; FastMCP is the implementation library.
- 150-line limit: the seven target modules keep each concern small; if `mcp_server.py`
  outgrows the limit, tool handlers split into `infra/mcp_tools_game.py` (commit/reveal/
  claim) and `infra/mcp_tools_meta.py` (handshake/audit).

## 6. Alternatives Considered & Justification

- **Central relay server** — forbidden by the assignment's architecture (single point of
  failure and of trust); full decentralization is the point.
- **Raw HTTP/WebSocket protocol** — rejected: MCP is non-replaceable by rule; FastMCP also
  gives typed tool schemas for free.
- **A2A / ACP additions** — recommended-only in the rulebook; skipped to keep the surface
  small (documented as a considered alternative).
- **Threads-in-one-process for the two peers during dev** — rejected outright: violates
  rules #1/#2 even in development; two subprocesses from Stage 2 onward.
- **Polling loop without deadlines** — rejected; the rulebook explicitly brands an
  expiry-less wait as "the direct recipe for deadlock".

## 7. Success Criteria & Test Scenarios

1. **Given** two peer processes on localhost 8801/8802, **when** peer A sends a geometric
   message, **then** peer B receives and decodes it correctly (M2 milestone).
2. **Given** state COMMITTING, **when** `transition("VERIFYING")` is requested, **then**
   `IllegalTransitionError` is raised immediately (state unchanged).
3. **Given** the full happy path, **then** the machine walks WAITING_FOR_OPPONENT →
   COMPUTING_MOVE → COMMITTING → AWAITING_REVEAL → VERIFYING → WAITING_FOR_OPPONENT.
4. **Given** an opponent that never answers a reveal request, **when** 30 s + 3 retries
   (5 s backoff) elapse, **then** the phase machine transitions AWAITING_REVEAL →
   TECHNICAL_LOSS and the turn closes cleanly (no hang; scored 0/0).
5. **Given** a main loop frozen (heartbeats stop), **when** 60 s pass, **then** the
   watchdog persists state to disk and returns SHUTDOWN; the persisted snapshot reloads.
6. **Given** TECHNICAL_LOSS, **when** any transition is attempted, **then** rejected
   (terminal state).
7. **Given** mismatching `config_sha256` values at handshake, **then** the peer refuses to
   start the game.
8. **Given** league mode with `opponent_url` on 127.0.0.1, **then** startup is refused
   with a clear "tunnel required" error; **given** an ngrok URL, a full round completes
   against a remote machine (M5 milestone).
9. **Edge:** duplicate `receive_commit` for the same step → idempotent ack, no state
   corruption; out-of-order `ack` for a future step → rejected; tunnel drops mid-turn →
   deadline path fires (no deadlock), watchdog stays quiet if the loop itself is alive.
10. **Separation test:** launching both roles from the same checkout produces two PIDs,
    two config dirs, and no cross-process writes (asserted via state-file paths).

## 8. Out of Scope

- Commit-reveal hashing, nonce handling, Step-0, audit verification math
  (PRD_commit_reveal.md — this layer only *transports* those payloads).
- Move choice and belief (PRD_strategy.md); hint generation (PRD_scent_language.md).
- Gmail reporting and the Gatekeeper rate-limiting of *email* traffic
  (PRD_reporting_gatekeeper.md); GUI banner rendering (PRD_gui_replay.md).
- Automatic tunnel process management (ngrok is started by the operator; we consume the URL).
