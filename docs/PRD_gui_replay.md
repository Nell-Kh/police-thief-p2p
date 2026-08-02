# PRD — Live GUI (Local Truth) and Replay Viewer (Cryptographic Witness)

**Project:** police-thief-p2p | **Version:** 1.00 | **Status:** awaiting approval
**Parent docs:** docs/PRD.md §3.7, docs/PLAN.md §1.4 (ADR-5) | **Rulebook:** ch. 7, Appendix ג, Appendix ה
**Dev priority:** Stage 7 (rulebook ch. 10) — the outer shell, built last.

---

## 1. Purpose & Theoretical Background

Observability is an integral component of a distributed system, split along two non-overlapping
axes (rulebook §7.2): the **Live GUI** answers "what is happening now?"; the **Replay Viewer**
answers "did what happened in the past really happen as claimed?".

**Local truth (אמת מקומית).** Each agent's observation Ωᵢ in the Dec-POMDP is a partial subset
of the true state S. The GUI is therefore bound to display **only** what its own agent can
know: its own position, its barriers knowledge, the *opponent's* sensed scent field, received
hints, and its own probabilistic belief map. There is **no bird's-eye view**; an interface
exposing the full objective state S violates the game rules and disqualifies the project
(rules #8/#9). Each side — cop and thief — runs its **own** GUI process, fully symmetric.

**Replay as witness.** With no central judge, history lives in a local log at each player —
a standing temptation to rewrite the past. Chapter 5's commit-reveal turns the log into
evidence; the Replay Viewer is the courtroom: it re-verifies every step's SHA-256 commitment
live while stepping through the match. Building it is a **mandatory submission requirement**
(rule #20), and screenshots of both tools are mandatory submission artifacts (Appendix ג).

## 2. Binding Parameters Used

| Parameter (Appendix ו) | Config key | Value | Status |
|---|---|---|---|
| Board size [גודל הלוח] | `board_and_agents.grid_size` | 7×7 | Minimum |
| Axis origin [ראשית מערכת הצירים] | `board_and_agents.axis_origin_corner` | top-left | Negotiation |
| Axis start index [אינדקס התחלת הצירים] | `board_and_agents.axis_start_index` | 0 | Negotiation |
| Scent field size [גודל שדה הריח] | `pheromones.pheromone_grid_size` | 5×5 | Fixed |
| Scent focus intensity [עוצמת הריח במוקד] | `pheromones.pheromone_center_intensity` | 0.9 | Fixed |
| Log file name [קובץ היומן] | derived from `game_id` | `log_<game_id>_g<NN>.json` | Fixed naming |

The heatmap renders the belief matrix of size `grid_size`; the axis parameters orient drawing
(row 0 at top by default, ADR-4). No GUI value is hardcoded — all read via `shared/config.py`.

## 3. Functional Requirements

### Live GUI (`gui/live.py`, `gui/heatmap.py`, `gui/banner.py`)

- **FR-1 Per-side window.** Each peer process opens its own Tkinter window titled with role and
  team; cop and thief GUIs are separate processes with separate configs (rule #1).
- **FR-2 Local truth only.** Rendered data is limited to: own position, known barriers, the
  opponent's scent field as sensed, received hints (text), own belief map, step counter, score
  context. The opponent's true position is **never** drawn. Enforced structurally: the GUI is
  fed a `LocalView` DTO from the SDK that simply does not contain opponent ground truth.
- **FR-3 Belief heatmap.** The agent's belief matrix is drawn as a `grid_size`×`grid_size` cell
  grid where **higher probability ⇒ deeper red** (progressively intensifying reds; zero belief
  = neutral background; barrier cells drawn dark with zero belief). Updated every turn after the
  belief update, so the "focus of suspicion" is visible at a glance.
- **FR-4 Turn banner.** A banner widget with exactly two states driven by the phase machine:
  **YOUR TURN** (green) when the opponent's MCP server handed the turn over; **LOCKED** (gray)
  from the moment the local move is committed and transmitted until the turn returns.
- **FR-5 Async turn lock.** While LOCKED, all move input (clicks/keys) is **ignored** — the
  banner is the visual face of the asynchronous state machine and prevents the race condition
  of both sides acting on the same step. Input handlers check the lock flag before dispatching.
- **FR-6 No business logic in GUI.** GUI files only render state and forward user events to the
  SDK (`sdk/sdk.py`); belief math, verification and rules live in `domain/` (guidelines:
  GUI excluded from coverage via pyproject `omit`, so everything testable stays out of `gui/`).

### Replay Viewer (`gui/replay.py`, verification in `domain/audit.py`)

- **FR-7 Log loading.** Load a final match log `log_<game_id>_g<NN>.json` (post final-reveal:
  every step entry carries commit hash, revealed fields **and** nonce) chosen via file dialog or
  `--log` CLI argument (`uv run python -m police_thief replay --log <path>`).
- **FR-8 Time navigation.** Step **forward/back** buttons walk the log one step at a time,
  rendering the board/hint/commit data of that step; jump-to-start/end conveniences allowed.
- **FR-9 Live per-step re-verification.** For every displayed step the viewer calls
  `domain.audit.verify_step`, which recomputes SHA-256 over the **full committed record**
  `{state, move, intent, hint, step, role, sub_game, nonce}` as canonical JSON — explicitly
  **not** the book's simplified `nonce|move` sketch (rulebook §7.5 caveat) — and compares to
  the stored commitment with `secrets.compare_digest`.
- **FR-10 Verdict rendering.** Match ⇒ green **"Verified OK"** stamp on the step; mismatch ⇒
  bright red **"TAMPERED"** banner, the viewer marks the game **disqualified immediately**, and
  the whole-match verdict is TAMPERED — **one failing step voids the entire match** (no appeal,
  no retroactive fix). A whole-log verdict summary (all steps) is always displayed.
- **FR-11 Submission artifacts.** The two mandatory screenshots — live belief heatmap and
  Replay Viewer showing "Verified OK" — are captured from these tools and stored under
  `assets/` for the academic README of both repos (Appendix ג checklist).

## 4. Input/Output Contracts

```python
# sdk/sdk.py (consumed by GUI; produced from domain state)
@dataclass LocalView:
    role: str                      # "police" | "thief"
    step: int
    my_pos: tuple[int, int]
    barriers: set[tuple[int, int]]
    opponent_scent: list[list[float]]   # grid_size x grid_size, values in [0, 0.9]
    belief: list[list[float]]           # grid_size x grid_size, rows sum ~1.0
    last_hint: str
    my_turn: bool                       # drives banner + input lock

# gui/heatmap.py
def belief_to_color(p: float, p_max: float) -> str     # probability -> "#rrggbb" red ramp
class HeatmapCanvas(tk.Canvas):
    def render(view: LocalView) -> None

# gui/banner.py
class TurnBanner(tk.Frame):
    def set_state(my_turn: bool) -> None               # green YOUR TURN / gray LOCKED
class InputLock:
    def allows(event) -> bool                          # False while LOCKED

# gui/replay.py
class ReplayViewer:
    def load(log_path: Path) -> None                   # parses log_<game_id>_g<NN>.json
    def step_forward() -> None
    def step_back() -> None
    def current_verdict() -> StepVerdict               # from domain.audit.verify_step
    def match_verdict() -> str                         # "VERIFIED_OK" | "TAMPERED"

# domain/audit.py (shared with PRD_commit_reveal.md — single source of verification truth)
def verify_step(reveal: dict, nonce: str, h_commit: str) -> StepVerdict
```

Log entry schema consumed by the viewer (per step, produced by `domain/logbook.py`):
`{"step": int, "role": str, "h_commit": str, "state": str, "move": str, "intent": str,
"hint": str, "sub_game": int, "nonce": str}` — nonces present only in the finalized log.

## 5. Constraints & Mandatory-Rule References (Appendix ה)

- **#8** Live UI displays local truth only — violation disqualifies the system's legality.
- **#9** Displaying the full objective board state is forbidden — project disqualification.
- **#19** Any hash mismatch ⇒ technical disqualification (the viewer surfaces this verdict).
- **#20** Building the replay/verification viewer is a threshold submission condition.
- Ch. 7 MANDATORY box: single TAMPERED disqualifies the game immediately; no appeal;
  screenshots (Verified OK + live belief map) are part of the submission (Appendix ג; README
  requirement #5 in ch. 9 — "absolute obligation").
- Verification must cover the **full committed record**, not the simplified sketch (ch. 1–7
  digest checklist item #20).
- Guidelines: `gui/` excluded from coverage in pyproject `omit`; therefore **all** verification
  logic resides in `domain/audit.py` (≥ 85% covered); no business logic in GUI; every file
  ≤ 150 code lines; Tkinter from stdlib (ADR-5); English-only comments; zero hardcoded values.

## 6. Alternatives Considered & Justification

- **PyQt / web dashboard vs. Tkinter** — Tkinter chosen (ADR-5): stdlib, zero extra dependency,
  fully sufficient for a heatmap grid, a two-state banner and replay buttons; PyQt licensing
  and packaging weight buy nothing required. A web UI would tempt shared state between peers.
- **Verification inside `gui/replay.py` vs. in `domain/audit.py`** — domain chosen: GUI is
  coverage-exempt, so verifier code there would be untested; sharing one verifier with the
  end-of-game audit guarantees the replay verdict and the live audit can never diverge.
- **Simplified `SHA256(nonce|move)` verification (book sketch)** — rejected; the book itself
  flags it as an illustration. Real verification recomputes the canonical-JSON rich record.
- **Single combined GUI showing both agents** — rejected outright: it is exactly the forbidden
  bird's-eye view (#9). Even for local development, two windows from two processes.
- **Matplotlib heatmap embedded in Tk** — rejected: heavyweight dependency for a colored grid;
  a plain Canvas with a red color ramp meets the "deeper red = higher probability" rule.

## 7. Success Criteria & Test Scenarios

Domain-level tests (GUI itself is coverage-exempt; logic is tested via `domain/` and DTOs):

- **T-1 Color ramp.** Given probabilities 0.0 < p₁ < p₂ ≤ p_max, when `belief_to_color` maps
  them, then p₂'s red channel dominance is ≥ p₁'s (monotone deepening), and p=0 returns the
  neutral background color.
- **T-2 Local-truth DTO.** Given a full game state, when `LocalView` is built for the cop, then
  it contains no thief ground-truth position field at all (schema assertion), and vice versa.
- **T-3 Input lock.** Given `my_turn=False`, when a synthetic click event is dispatched, then
  `InputLock.allows` is False and no move callback fires; given `my_turn=True`, it fires once.
- **T-4 Banner states.** Given phase transitions COMMITTING→AWAITING_REVEAL→…→
  WAITING_FOR_OPPONENT, when the banner observes them, then it shows LOCKED until the turn
  returns, then YOUR TURN (green).
- **T-5 Clean replay.** Given an honest finalized 35-step log, when the viewer steps through
  all steps, then every `current_verdict().ok` is True and `match_verdict()` == "VERIFIED_OK".
- **T-6 Tampered replay.** Given the same log with one character of step 12's hint altered
  (commit hash untouched), when replayed, then step 12 verdict is TAMPERED, `match_verdict()`
  == "TAMPERED", and the disqualification flag is set — one failure voids the whole match.
- **T-7 Edge — missing nonce.** Given a log that was never finalized (no nonces), when loaded,
  then the viewer reports "not auditable — final reveal missing" instead of a false Verified OK.
- **T-8 Edge — boundary navigation.** Given the viewer at step 0 / last step, when back /
  forward is pressed, then it clamps without error.
- **T-9 Screenshots exist.** Submission gate (M8): `assets/` contains a live belief-map
  screenshot and a replay "Verified OK" screenshot referenced from both repos' README.md.

## 8. File Split for the 150-Line Rule

`gui/live.py` (window shell, wiring of view updates), `gui/heatmap.py` (color ramp + canvas),
`gui/banner.py` (turn banner + input lock), `gui/replay.py` (loader, navigation, verdict
display). If `replay.py` outgrows 150 lines, split `replay_view.py` (widgets) from
`replay_ctl.py` (navigation/verdict control). The `LocalView` DTO lives in the SDK layer;
verification lives in `domain/audit.py` (see PRD_commit_reveal.md §8).

## 9. Out of Scope

- Belief-map computation and hint trust math (PRD_strategy.md / PRD_scent_language.md — the GUI
  only renders the resulting matrix).
- Commitment creation, audit algorithms and log writing (PRD_commit_reveal.md — reused, not
  reimplemented).
- Any spectator/observer mode showing both sides (forbidden by rule #9).
- Animations, sound, replay export to video — cosmetic, not required by the rulebook.
- Serving the GUI remotely / multi-machine display.
