# PRD — Strategy Module: Brains, Belief-Driven Decision Policy (Stage 3)

**Project:** police-thief-p2p | **Version:** 1.00 | **Status:** awaiting approval
**Parent documents:** docs/PRD.md §3.5, docs/PLAN.md §1.4, ADR-2 | **Rulebook source:**
Chapter 6 (+ Appendix ה rule #25; Appendix ו Table 22)
**Target modules:** `src/police_thief/domain/brain/base.py`, `brain/heuristic.py`,
`brain/police.py`, `brain/thief.py`, `brain/pathfind.py`, plus `domain/belief.py` (shared
with the scent PRD, which owns its Bayesian update; this PRD owns its *consumption*)

---

## 1. Purpose & Theoretical Background

The strategy module is "where the grade lives" (Appendix ד): the mandated, **separate**
decision component that turns partial observations into legal moves. The rulebook states a
clear development requirement — a distinct strategy module plugged into the **PeerRuntime**
at a precise point: **immediately after decoding the incoming hint, and before packing the
outgoing Commit**. Between those two points sit all of the agent's intelligence: belief
update, legal-move choice, and (delegated to the verbal layer) deception-text composition.

In Dec-POMDP terms the brain maps the local observation history (own position, opponent's
scent field, trust-weighted hints) to an action maximizing expected reward under the
scoring table. Chapter 6 offers three equal tracks: pure Bayes+Manhattan heuristics, a
richer custom heuristic, or (optional, untaught) RL. Per **ADR-2** we take the **enhanced
heuristic** track: Bayesian belief map with argmax targeting, **barrier-aware BFS distance
fields instead of raw Manhattan** (Manhattan ignores walls — exactly what barriers create),
trust-weighted hint fusion, deliberate cop barrier planning, and thief evasion maximizing
expected true-path distance. The **LLM never picks moves** (ch. 6 warning box; Appendix ה
#25): LLMs hallucinate in Cartesian space; movement stays with deterministic Python.

## 2. Binding Parameters Used

| Parameter | Config key | Value | Status |
|---|---|---|---|
| Board size | `board_and_agents.grid_size` | 7 | minimum |
| Move set | `movement_and_barriers.move_set` | N/S/E/W/STAY | fixed |
| Barrier quota | `movement_and_barriers.max_barriers` | 14 | minimum |
| Step ceiling / survival threshold | `max_moves` / `survival_threshold` | 35 / 35 | minimum |
| Scoring (reward signal R) | `scoring.*` | 20/5, 5/10, tie 2, tech 0 | fixed |
| Thief brain class (private) | TOML `[strategy] thief_class` | `police_thief.domain.brain.thief:ThiefHeuristicBrain` | private per peer |
| Police brain class (private) | TOML `[strategy] police_class` | `police_thief.domain.brain.police:PoliceHeuristicBrain` | private per peer |

`[strategy]` keys use `package.module:Class` notation; an empty section runs the built-in
heuristic brain (`brain/heuristic.py`). Brain choice is private, never negotiated.

## 3. Functional Requirements

- **FR-1 Plug-in point.** The brain is invoked by PeerRuntime exactly once per own turn,
  after hint decode / before commit pack, receiving a read-only `DecisionContext`. It never
  performs I/O, never calls MCP, never calls an LLM.
- **FR-2 BrainBase contract.** `base.py` defines `BrainBase` with the overridable
  `_pick_move(ctx) -> Move` and, for the cop, `_decide_move(ctx) -> Decision` where
  `Decision` is either a movement or a barrier placement (a barrier is only choosable in a
  no-movement turn). The public entry `decide()` template-method wraps legality filtering:
  **whatever a subclass returns is validated against `Rules.legal_moves`; an illegal
  proposal is replaced by the best legal fallback** (defense in depth, ch. 6 exception box).
- **FR-3 Belief targeting.** Both brains read the Bayesian belief map (opponent-position
  distribution over all cells, barriers pinned to zero) and use `argmax b(s)` as the
  target estimate; ties in the argmax break deterministically (row-major order).
- **FR-4 Barrier-aware BFS distance field.** `pathfind.py` computes, by breadth-first
  search from a source cell over the 4-neighborhood **excluding barrier cells**, the exact
  shortest-path step count to every reachable cell (unreachable = ∞). This replaces raw
  Manhattan distance, which under-counts around walls; on a barrier-free board the two
  coincide (property test).
- **FR-5 Cop policy** (`police.py`): (a) move to minimize BFS distance to the belief
  argmax; (b) **barrier planning** — in a candidate no-movement turn, evaluate placements
  (self-cell or 4-adjacent) that block the thief's highest-value escape corridors
  (cells whose blocking maximally raises the thief's expected BFS distance to freedom /
  reduces his reachable region), subject to: never place a barrier that increases the
  cop's own distance to the belief argmax above a threshold (**no self-trapping**), and
  **quota management** — reserve a configurable endgame reserve (default: keep ≥ 4 of the
  14 until the thief's reachable region is under a size threshold); (c) prefer a trapping
  placement (barrier onto the thief's believed cell) only when belief mass there exceeds a
  confidence threshold, since a miss burns quota; (d) issue a Capture Claim decision when
  own cell equals the believed thief cell and physics confirms overlap.
- **FR-6 Thief policy** (`thief.py`): move to **maximize the expected BFS distance from
  the cop-belief distribution** (expectation over the belief map, not just its argmax);
  **corridor avoidance** — penalize moves into cells with low escape degree (few
  non-barrier neighbors) and into regions whose reachable area is small (anti-trap);
  survival-aware: as the step counter approaches `survival_threshold`, weight safety
  (distance floor) over distance maximization.
- **FR-7 Deterministic tie-breaking.** All scoring ties break by a fixed move-order
  (N, S, E, W, STAY) — reproducible runs, testable decisions, byte-stable replays.
- **FR-8 LLM exclusion.** No code path in `domain/brain/` imports or invokes any
  `infra/llm` provider. The documented mutual-agreement exception (ch. 6) is **not taken**;
  even if a future agreement allowed it, FR-2's legality filter would remain in force.
- **FR-9 Configurable loading.** A small factory resolves `[strategy]` keys via
  `importlib`, verifies the class subclasses `BrainBase`, and falls back to the built-in
  heuristic on an empty section (reference-implementation behavior).
- **FR-10 Blind mode (Stage 3).** With a fully known opponent position injected as a
  degenerate belief (probability 1 on one cell), the cop brain computes and follows the
  shortest path autonomously — the M3 milestone — isolating decision correctness from
  uncertainty noise.

## 4. Input/Output Contracts

```python
# domain/brain/base.py
@dataclass(frozen=True)
class DecisionContext:
    board: BoardState                 # own position, barriers, step (local truth)
    role: Role                        # COP | THIEF
    belief: BeliefMap                 # P(opponent at cell), sums to 1, barriers = 0
    legal_moves: list[Move]           # precomputed by Rules for this turn
    barriers_left: int                # cop only: quota remaining
    steps_remaining: int              # survival_threshold - step
    rules: Rules                      # pure query API (no mutation)

@dataclass(frozen=True)
class Decision:
    kind: Literal["move", "barrier", "claim"]
    move: Move | None                 # kind == "move"
    barrier_cell: Cell | None         # kind == "barrier" (implies no movement this turn)

class BrainBase(ABC):
    def decide(self, ctx: DecisionContext) -> Decision   # template method + legality guard
    @abstractmethod
    def _pick_move(self, ctx: DecisionContext) -> Move
    def _decide_move(self, ctx: DecisionContext) -> Decision   # cop override: barrier choice

# domain/brain/pathfind.py
def bfs_distance_field(size: int, barriers: frozenset[Cell],
                       source: Cell) -> dict[Cell, int]     # unreachable cells absent (∞)
def reachable_region(size: int, barriers: frozenset[Cell], source: Cell) -> frozenset[Cell]
def escape_degree(size: int, barriers: frozenset[Cell], cell: Cell) -> int  # 0..4

# domain/brain/police.py / thief.py
class PoliceHeuristicBrain(BrainBase):
    def _decide_move(self, ctx) -> Decision       # movement vs. barrier vs. claim
    def _score_barrier(self, ctx, cell: Cell) -> float   # corridor value - self-trap penalty
class ThiefHeuristicBrain(BrainBase):
    def _pick_move(self, ctx) -> Move
    def _expected_cop_distance(self, ctx, cell: Cell) -> float  # E over belief of BFS dist

# domain/brain/heuristic.py — built-in default (empty [strategy] section)
class HeuristicBrain(BrainBase): ...              # role-dispatching thin wrapper
```

The belief map itself (construction, Bayes update, trust weighting) is produced upstream
by `domain/belief.py` (see PRD_scent_language.md); the brain treats it as immutable input.

## 5. Constraints & Mandatory-Rule References

- Rulebook §6.2 — **separate strategy module is a clear development requirement**, plugged
  in after hint-decode / before commit-pack (enforced by PeerRuntime's single call site).
- Appendix ה **#25** + ch. 6 warning box — the LLM must not decide movement (Appendix ה
  grades it a recommendation; ch. 6's box is a binding prohibition subject only to a
  documented mutual-agreement exception, which we do not take). Our constraint is absolute.
- **#13/#14** via FR-2's legality guard — the brain can never emit a diagonal or blocked
  move to the protocol layer.
- Barrier law constraints (#15/#16, #46/#47) are enforced by `Rules`; the brain only
  *chooses among* legal barrier options surfaced by it.
- 150-line limit: five brain files + pathfind keep concerns small; if `police.py` outgrows
  the limit, barrier planning moves to `brain/barrier_plan.py`.

## 6. Alternatives Considered & Justification

- **Q-Learning / RL (rejected — documented decision, ADR-2).** The rulebook stresses RL is
  optional and untaught in the course; training cost, non-determinism, and convergence risk
  against a changing opponent population buy no grade requirement. Heuristics are
  transparent, debuggable, and per the book "often fully competitive with RL".
- **Raw Manhattan distance (reference default) — rejected as sole metric.** Admissible on
  an empty board but blind to barriers: the cop would happily walk into his own wall.
  BFS distance is exact on the barrier graph at trivial cost (≤ 49 cells at the 7×7 floor).
- **Minimax/expectimax search over the joint state** — deferred: the belief-space branching
  is large and BFS + belief targeting already meets the KPIs; noted as a future extension.
- **LLM-based movement policy (allowed only by mutual agreement)** — not taken;
  hallucination risk and no unilateral legality (ch. 6 exception box).

## 7. Success Criteria & Test Scenarios

1. **Given** a degenerate belief (thief known at (5,5)), cop at (0,0), empty board,
   **when** the cop brain plays repeatedly, **then** it reaches (5,5) in exactly 10 moves
   — BFS-shortest path, no manual intervention (M3 milestone).
2. **Given** a wall of barriers between cop and target, **then** BFS distance > Manhattan
   distance and the chosen move follows the true shortest path around the wall.
3. **Given** an empty board, **then** for random cell pairs BFS distance == Manhattan
   distance (property-based test).
4. **Given** two moves with equal score, **then** the N,S,E,W,STAY order decides —
   repeated runs produce identical decisions (determinism test).
5. **Given** a candidate barrier that would raise the cop's own path to the belief argmax
   to ∞ (self-trap), **then** `_score_barrier` rejects it in favor of movement.
6. **Given** 11 of 14 barriers used and a large thief reachable-region, **then** the cop
   defers further placements (endgame reserve honored).
7. **Given** thief belief mass 0.9 on the thief's actual cell adjacent to the cop,
   **then** the cop chooses the trapping placement and the engine scores a capture.
8. **Given** a thief between two corridors, one 1-cell wide and one open, with equal cop
   distance, **then** the thief picks the open region (corridor avoidance / escape degree).
9. **Given** a subclass whose `_pick_move` returns an illegal move (mock), **then**
   `decide()` substitutes a legal fallback and flags a warning (never propagates).
10. **Given** `[strategy]` empty → `HeuristicBrain` loads; **given**
    `thief_class = "x.y:NotABrain"` (not a `BrainBase`) → configuration error at startup.
11. **Edge:** belief uniformly flat (no information) → cop still produces a legal move
    (deterministic patrol toward the board center); thief fully enclosed except one exit →
    picks the exit; `steps_remaining == 1` → thief prefers any capture-safe move.
12. **Static test:** no module under `domain/brain/` imports from `infra.llm` (FR-8).

## 8. Out of Scope

- Bayesian belief construction, scent modeling, trust coefficient, lie detection
  (PRD_scent_language.md) — consumed here as `BeliefMap` input.
- Hint/deception text generation (verbal layer; the Intent flag is sealed at commit-pack).
- Commit-reveal packing (crypto PRD); turn scheduling and transport (P2P PRD).
- RL infrastructure of any kind; opponent modeling beyond the belief map.
