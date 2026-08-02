# PRD — Board, Physics & Scoring Engine (Stage 1)

**Project:** police-thief-p2p | **Version:** 1.00 | **Status:** awaiting approval
**Parent documents:** docs/PRD.md §3.1, docs/PLAN.md §1.4 | **Rulebook source:** Chapter 3 (+ Appendix ו Tables 13, 15, 17; Appendix ה rules #11–#16, #46–#48)
**Target modules:** `src/police_thief/domain/board.py`, `domain/rules.py`, `domain/scoring.py`

---

## 1. Purpose & Theoretical Background

The board engine is the physical core of the Dec-POMDP: it implements the state space S
(agent coordinates + barrier layout), the physical part of the action spaces {Aᵢ}
(movement, barrier placement), the deterministic transition function P, and the reward
function R derived from the scoring table. Because the game has **no central server and no
referee**, physics is enforced *by each agent independently* against the same shared,
signed contract (`config/game.json`): both peers must compute byte-identical outcomes from
identical inputs. Any move the opponent proposes is validated locally; an illegal move is
rejected by the receiving side ("the opponent enforces the physics", rulebook §3.4).

This subsystem is pure domain logic: **no I/O, no networking, no LLM** — it runs
identically in a single-process simulation (development Stage 1) and inside each peer
process later. Everything downstream (strategy, scent, crypto, GUI) consumes its types.

## 2. Binding Parameters Used

All values are loaded from configuration (mirror of Appendix ו); none is hardcoded.

| Parameter (Appendix ו) | Config key (`config/game.json`) | Value | Status |
|---|---|---|---|
| Board size | `board_and_agents.grid_size` | 7 (7×7) | minimum |
| Number of agents | `board_and_agents.num_agents` | 2 | fixed |
| Coordinate origin | `board_and_agents.axis_origin_corner` | `top-left` | negotiation |
| Axis start index | `board_and_agents.axis_start_index` | 0 | negotiation |
| Start position — thief | `board_and_agents.thief_start` | [3, 3] | negotiation |
| Start position — cop | `board_and_agents.cop_start` | [0, 0] | negotiation |
| Move set | `movement_and_barriers.move_set` | N, S, E, W, STAY | fixed |
| Barrier quota | `movement_and_barriers.max_barriers` | 14 | minimum |
| Step ceiling | `movement_and_barriers.max_moves` | 35 | minimum |
| Survival threshold | `movement_and_barriers.survival_threshold` | 35 | minimum |
| Capture score — cop / thief | `scoring.capture_cop` / `scoring.capture_thief` | 20 / 5 | fixed |
| Survival score — cop / thief | `scoring.survival_cop` / `scoring.survival_thief` | 5 / 10 | fixed |
| Tie score | `scoring.tie_score` | 2 | fixed |
| Technical loss | `scoring.technical_loss` | 0 (both sides) | fixed |

Coordinate convention (ADR-4, PLAN §5): cells are `(row, col)`, origin at the **top-left**
corner, 0-indexed, row axis grows **downward**. N = row−1, S = row+1, W = col−1, E = col+1.
"Minimum" values may only be raised by mutual agreement; "fixed" values never change.

## 3. Functional Requirements

- **FR-1 Grid model.** `Board` holds a square grid of side `grid_size` (validated ≥ 7),
  both agents' positions, and the set of barrier cells. Positions are always in-bounds.
- **FR-2 Move set.** Exactly five actions: `N`, `S`, `E`, `W`, `STAY`. One action per agent
  per turn. **Diagonal movement does not exist in the action space** (rules #13, #14).
- **FR-3 Move validation.** A move is legal iff the target cell is (a) inside the grid,
  (b) not a barrier cell. `STAY` is always legal for movement purposes. Validation is a
  pure function usable on *both* our own candidate moves and the opponent's revealed moves.
- **FR-4 Barrier law** (rulebook §3.4 framed box):
  (a) only the **cop** may place a barrier; (b) only in a turn in which he **forgoes
  movement**; (c) only on his **own cell or one of the four orthogonally adjacent** cells
  (in-bounds); (d) the cell becomes **impassable to both players until game end —
  irreversible**; (e) total placements ≤ `max_barriers`; placement #quota+1 is rejected;
  (f) every placement is **publicly and truthfully declared** with its exact location — the
  engine emits a declaration record for the protocol layer (rules #15, #16).
- **FR-5 Trapping placement.** A barrier placed on the cell the thief currently occupies is
  a **capture** (rule #46). The engine detects this at barrier application time.
- **FR-6 No-legal-move capture.** A thief with no legal move at all (all four neighbors
  blocked by barriers/board edges — `STAY` on a doomed cell does not rescue him per
  rulebook §3.4: "left with no legal move") is **captured** (rule #47). Evaluated after
  every barrier placement and at the start of the thief's turn.
- **FR-7 Overlap capture + claim.** When the cop's cell equals the thief's cell **and the
  cop declares a Capture Claim**, the game ends as a capture. The engine only *detects*
  overlap and validates the claim against positions; transporting the claim and the thief's
  cryptographically-truthful answer is the P2P/crypto layer's job (rules #21, #22).
- **FR-8 Survival & step ceiling.** The engine counts **valid steps**; when the thief
  completes `survival_threshold` (35) valid steps without capture, the game ends as
  survival. `max_moves` (35) bounds a mini-game's length; with the default equality the two
  conditions coincide — reaching the ceiling without capture is a thief survival win.
- **FR-9 Scoring.** `scoring.py` maps a terminal event to `(cop_score, thief_score)`:
  capture → (20, 5); survival → (5, 10); technical loss → (0, 0) for **both** sides
  (rule #48). Series tie (cumulative equality over all mini-games) → 2 points each side
  (Appendix ו Table 17); computed at series level, exposed as a pure function here.
- **FR-10 Config-driven construction.** All numeric values arrive via an injected config
  object; `Board.from_config()` validates minimum floors (e.g. rejects `grid_size < 7`,
  `max_barriers < 14`) and fixed-value integrity (rule #12).

## 4. Input/Output Contracts

```python
# domain/board.py
Cell = tuple[int, int]                      # (row, col), 0-indexed, top-left origin
Move = Literal["N", "S", "E", "W", "STAY"]

@dataclass(frozen=True)
class BoardState:
    grid_size: int
    cop: Cell
    thief: Cell
    barriers: frozenset[Cell]
    step: int                               # valid steps completed

class Board:
    @classmethod
    def from_config(cls, cfg: GameConfig) -> "Board": ...
    def state(self) -> BoardState: ...
    def target_cell(self, origin: Cell, move: Move) -> Cell: ...
    def in_bounds(self, cell: Cell) -> bool: ...

# domain/rules.py
class Rules:
    def is_legal_move(self, s: BoardState, role: Role, move: Move) -> bool: ...
    def legal_moves(self, s: BoardState, role: Role) -> list[Move]: ...
    def can_place_barrier(self, s: BoardState, cell: Cell,
                          placed_so_far: int) -> BarrierVerdict: ...
    def apply_move(self, s: BoardState, role: Role, move: Move) -> BoardState:
        """Raises IllegalMoveError on any violation (incl. diagonals by construction)."""
    def apply_barrier(self, s: BoardState, cell: Cell) -> tuple[BoardState, BarrierDecl]:
        """BarrierDecl = {'cell': Cell, 'step': int} — the mandatory public declaration."""
    def capture_by_overlap(self, s: BoardState) -> bool: ...
    def thief_trapped(self, s: BoardState) -> bool: ...
    def survival_reached(self, s: BoardState) -> bool: ...

# domain/scoring.py
class Outcome(Enum): CAPTURE, SURVIVAL, TECHNICAL_LOSS
def score(outcome: Outcome, cfg: GameConfig) -> tuple[int, int]   # (cop, thief)
def series_result(minigame_scores: list[tuple[int, int]], cfg: GameConfig) -> SeriesResult
```

`BarrierVerdict` is a small result type (`ok: bool, reason: str`) so rejections are
explainable in logs and to the opponent. All functions are deterministic and side-effect
free on `BoardState` (frozen dataclass ⇒ new state per application), which makes replay
verification and both-peers-compute-the-same-thing trivially testable.

## 5. Constraints & Mandatory-Rule References

- Appendix ה **#11** — config byte-identical on both sides (engine consumes, never mutates it).
- **#12** — minimum values raised only by agreement, never lowered; enforced in `from_config`.
- **#13/#14** — orthogonal moves only / no diagonals (excluded from the type itself).
- **#15/#16** — open, truthful barrier declaration; no lying about location (`BarrierDecl`).
- **#46/#47** — trapping placement = capture; thief with no legal move = captured.
- **#48** — score every ending per the table: capture 20/5, survival 5/10, technical 0/0.
- **#21/#22** — capture-claim truth duty (detection here; enforcement in the crypto layer).
- Files ≤ 150 code lines (guidelines): the split above (board/rules/scoring) is the plan;
  if `rules.py` approaches the limit, barrier logic moves to `domain/barriers.py`.

## 6. Alternatives Considered & Justification

- **Mutable single Board object** vs. immutable `BoardState` snapshots — immutable chosen:
  audit/replay and belief simulation need cheap historical states; mutation bugs are the
  classic source of divergent "local truths".
- **Graph library (networkx)** for adjacency — rejected: a 4-neighborhood on a ≤ dozens-side
  grid needs no dependency; keeps the engine trivially portable into both submission repos.
- **Encoding capture-on-claim inside the engine** — rejected: the claim is a protocol
  message with cryptographic truth duty; the engine stays pure and testable offline.
- **1-indexed / bottom-left axes** (ch. 6 figure convention) — rejected per ADR-4; the ch. 3
  top-left default is used and documented as our contradiction-log choice.

## 7. Success Criteria & Test Scenarios

Coverage ≥ 85%; all tests pytest, TDD-first. Key given/when/then scenarios:

1. **Given** a 7×7 board, cop at (0,0), **when** cop plays `N` (target (−1,0)),
   **then** `IllegalMoveError` — out of bounds.
2. **Given** any state, **when** a diagonal is attempted, **then** it is inexpressible:
   the `Move` type has five members (type-level test + validation test with raw string).
3. **Given** a barrier at (2,3), **when** thief moves onto (2,3), **then** rejected.
4. **Given** cop at (3,3), **when** he places a barrier at (5,3), **then** rejected
   (not self or 4-adjacent); at (4,3) → accepted + `BarrierDecl` emitted.
5. **Given** 14 barriers already placed (quota), **when** placement #15 is requested,
   **then** `BarrierVerdict(ok=False)` (M1 milestone: "barrier #15 rejected").
6. **Given** thief at (4,4), **when** cop places a barrier at (4,4), **then** outcome
   CAPTURE (trapping placement).
7. **Given** thief at (0,0) with (0,1) and (1,0) barriered, **when** trapped-check runs,
   **then** thief is captured (edge corner + barriers = no legal move).
8. **Given** step counter 34 without capture, **when** the thief completes valid step 35,
   **then** outcome SURVIVAL; `score` returns (5, 10).
9. **Given** outcome CAPTURE / TECHNICAL_LOSS, **then** `score` returns (20, 5) / (0, 0).
10. **Given** two mini-game score lists with equal cumulative totals, **when**
    `series_result` runs, **then** each side receives tie score 2.
11. **Given** `grid_size=5` in a config, **when** `Board.from_config` runs, **then**
    rejected (below the 7×7 minimum floor).
12. **Edge:** barrier placement in a movement turn → rejected; barrier by the thief →
    rejected (cop-only); `STAY` while adjacent to the thief → legal, no capture without
    overlap + claim.

## 8. Out of Scope

- Commit-reveal, signatures, capture-claim transport & audit (PRD_commit_reveal.md).
- Scent emission/decay and belief (PRD_scent_language.md) — consumers of `BoardState`.
- Move *selection* (PRD_strategy.md); networking (PRD_p2p_mcp.md); GUI (PRD_gui_replay.md).
- League bookkeeping (diversity reward, game counting) — reporting PRD.
