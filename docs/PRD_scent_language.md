# PRD — Pheromone Scent Model & Verbal Hint Layer (Stage 4)

**Project:** police-thief-p2p | **Version:** 1.00 | **Status:** awaiting approval
**Parent documents:** docs/PRD.md §3.4/§3.6, docs/PLAN.md §1.4, ADR-3
**Rulebook source:** Chapter 4, §6.5 (+ Appendix ה rules #23, #26/#27; Appendix ו Tables 14, 16, 21)
**Target modules:** `src/police_thief/domain/scent.py`, `domain/belief.py`,
`domain/trust.py`, `infra/llm/base.py`, `llm/template.py`, `llm/ollama.py`,
`llm/claude_api.py`, `llm/claude_cli.py`

---

## 1. Purpose & Theoretical Background

This subsystem creates the game's uncertainty — and the means to reason under it.
**Pheromones (stigmergy, ch. 4):** each agent — by the very act of **moving or staying** —
deposits a decaying scent field around its position. The scent is **natural and
unforgeable**: no agent can plant a false trail; each side emits its own field and
**reads only the opponent's**. The decaying trail (~6–7 turns readable at ρ=0.10) feeds a
Bayesian **belief map** and enables **lie detection**: when a verbal hint contradicts the
physical trail, the trustworthy environment wins.
**Verbal hints (§6.5):** free natural language is the **only** inter-agent information
channel about position — a numeric-position protocol is forbidden. Hints may be truthful
or lies (the `Intent` flag, sealed inside the commit); the LLM produces this rhetorical
layer only — never movement. Four provider modes trade token budget for banter richness;
a hard fallback chain guarantees a game always finishes.

## 2. Binding Parameters Used

| Parameter (Appendix ו) | Config key | Value | Status |
|---|---|---|---|
| Scent intensity at focus | `pheromones.pheromone_center_intensity` | 0.9 | **fixed** |
| Scent decay rate ρ | `pheromones.pheromone_decay` | 0.10 | **fixed** |
| Scent field size | `pheromones.pheromone_grid_size` | 5 (5×5) | **fixed** |
| Game arena | `world.map_area` | "Haifa" | negotiation |
| Hint word limit | `world.hint_max_words` | 15 | negotiation |
| Token estimate per series | `network_and_league.token_budget_per_series` | ~200 000 | negotiation |
| Verbal provider (private) | TOML `[trash_talk] provider` | `claude_api` (ours; book default `template`) | private per peer |
| Provider throttle (private) | TOML `[trash_talk] every_n_steps` | 3 | private per peer |

All three pheromone values are **fixed status** — never changeable. `map_area` and
`hint_max_words` are agreed terms, signed with the rest of the contract.

## 3. Functional Requirements

### Scent (domain/scent.py)

- **FR-1 Emission.** On every own action — movement **or** STAY — a 5×5 emission window is
  applied centered on the agent's cell, clipped at board edges. The fixed radial matrix
  (row/col offsets −2..+2; rulebook Figure 4, verbatim — center 0.90, orthogonal 0.62,
  diagonal ring 0.42, outer rings 0.20/0.14/0.04; a constant of the locked model):

  ```
  0.04 0.14 0.20 0.14 0.04
  0.14 0.42 0.62 0.42 0.14
  0.20 0.62 0.90 0.62 0.20
  0.14 0.42 0.62 0.42 0.14
  0.04 0.14 0.20 0.14 0.04
  ```

- **FR-2 Decay.** At the end of every **full turn** (after both agents have moved), every
  cell of every scent field updates by
  `τ_ij(t+1) = max(0, (1 − ρ) · τ_ij(t) + Δτ_ij)` with ρ = 0.10. Values stay in [0, 0.9];
  the max(0,·) clamp means "quiet" is absence of information, never negative information.
- **FR-3 Per-side fields, opponent-only reads.** Two independent `ScentField` instances
  (cop-emitted, thief-emitted); each agent is exposed **only to the opponent's** field —
  own-field reads are blocked at the SDK surface (local-truth discipline).
- **FR-4 Unforgeability by construction.** Emission is triggered exclusively by the
  physics engine applying a validated move; no public API deposits arbitrary scent. The
  only possible "manipulation" is legal: staying/returning strengthens your own true cell
  — a cost, not a weapon.
- **FR-5 Pre-series cryptographic locking (rule #23).** The peer exports a canonical model
  description — formula text, ρ, center intensity, the full 5×5 matrix, and a numeric
  worked example (center τ=0.9; after one decay turn 0.9·(1−0.10)=0.81) — and computes its
  SHA-256. The hash is exchanged and must match the opponent's before mini-game 1, making
  any later behavioral deviation detectable. Sharing the scent code itself with the
  opponent is supported (book: recommended).

### Belief & trust (domain/belief.py, domain/trust.py)

- **FR-6 Bayesian belief map.** `BeliefMap` is a `grid_size`×`grid_size` distribution over
  the opponent's location: prior = previous belief diffused by opponent-movement
  possibilities; likelihood from the opponent's scent field (fresh τ ⇒ high presence
  likelihood); barrier cells pinned to 0; renormalized each turn.
- **FR-7 Hint fusion with trust weighting.** Each decoded hint contributes a likelihood
  term weighted by the trust coefficient `w ∈ [0,1]` (neutral start 0.5):
  belief ∝ scent-likelihood × (w·hint-likelihood + (1−w)·uniform).
- **FR-8 Lie detection.** For each hint, compare the expected fresh-trace intensity in the
  hinted region — "moved north" predicts τ ≈ (1−ρ)·0.9 ≈ 0.81 there — with the measured
  field. A large gap (measured ≈ 0.00 vs expected 0.81) lowers `w` (multiplicative
  decrease, floor > 0); consistency raises it slowly. The contradiction redirects belief
  mass toward the true scent concentration — the lie becomes a double-edged sword.

### Verbal layer (infra/llm/*)

- **FR-9 Free natural language only.** Hints are free-text sentences (rules #26/#27):
  never coordinates, never an encoded numeric-position protocol. Outbound hints are
  linted: any coordinate-like pattern fails validation and is regenerated or replaced by a
  template sentence.
- **FR-10 Word cap.** `hint_max_words` (15) is enforced twice: hard truncation/validation
  on every outbound hint (template AND LLM output), and stated inside the LLM system
  prompt so the model targets it natively.
- **FR-11 Arena flavor.** With `map_area = "Haifa"` (the shipped arena), hints weave real
  landmarks ("slipping past the Bahá'í Gardens") — in template mode too; an arena with no
  landmark pool ⇒ generic landmarks. `test_the_shipped_arena_has_real_landmarks` fails if
  the committed arena ever loses its pool.
- **FR-12 Intent flag.** The brain/runtime decides `truth`/`lie` per hint; the provider is
  told which to produce; the flag is **sealed inside the commit record** (crypto layer) so
  post-hoc "I meant to lie" claims are impossible.
- **FR-13 Four providers, one interface.** `HintProvider` implementations: `template`
  (pre-made sentences, zero tokens, offline — book default and our **fallback**), `ollama`
  (local, `localhost:11434`, zero API tokens), `claude_api` (Haiku — **our pick**, ADR-3),
  `claude_cli` (`claude -p`, highest cost; implemented for completeness, unused by default).
- **FR-14 Throttle & budget.** `every_n_steps = 3`: the LLM is called at most every third
  step; other steps use the template. Token usage per call is metered, accumulated against
  the ~200k series budget, and included in the end-of-game report (rule #54); crossing a
  90% budget guard forces template mode for the rest of the series.
- **FR-15 Hard fallback chain.** Any provider failure — API error, rate limit, step-
  deadline timeout, budget exhaustion, malformed output — falls back to `template` for
  that hint (after repeated failures, for the session). **A game must always finish
  regardless of any LLM outage.**

## 4. Input/Output Contracts

```python
# domain/scent.py
EMISSION_MATRIX: tuple[tuple[float, ...], ...]   # the 5x5 constant of FR-1
class ScentField:
    def __init__(self, grid_size: int, cfg: PheromoneConfig): ...
    def emit(self, center: Cell) -> None          # clip at edges; called by physics only
    def decay(self) -> None                       # full-turn decay, FR-2 formula
    def read(self) -> list[list[float]]           # snapshot for the *opponent's* reader
def model_lock_payload(cfg: PheromoneConfig) -> str  # canonical text: matrix + example
def model_lock_sha256(cfg: PheromoneConfig) -> str   # hex digest exchanged pre-series

# domain/belief.py
class BeliefMap:
    def __init__(self, grid_size: int, barriers: frozenset[Cell]): ...
    def update(self, opponent_scent: list[list[float]],
               hint: DecodedHint | None, trust: float) -> None
    def argmax(self) -> Cell                      # deterministic tie-break (row-major)
    def prob(self, cell: Cell) -> float
    def as_matrix(self) -> list[list[float]]      # GUI heatmap input

# domain/trust.py
class TrustTracker:
    value: float                                   # w in [floor, 1], starts 0.5
    def score_hint(self, hint: DecodedHint, opponent_scent: list[list[float]],
                   rho: float) -> HintVerdict      # {expected, measured, contradiction}
    def update(self, verdict: HintVerdict) -> float

# infra/llm/base.py
@dataclass(frozen=True)
class HintRequest:
    role: Role; intent: Literal["truth", "lie"]; map_area: str
    max_words: int; context: HintContext           # own move direction, step, banter seed
@dataclass(frozen=True)
class HintResult:
    text: str; tokens_in: int; tokens_out: int; provider: str
class HintProvider(ABC):
    @abstractmethod
    def generate(self, req: HintRequest) -> HintResult    # raises ProviderError
def validate_hint(text: str, max_words: int) -> str       # word cap + no-numeric lint
def build_provider(cfg: TrashTalkConfig, meter: TokenMeter) -> HintProvider
    # wraps the chosen provider in throttle + budget guard + template fallback
```

## 5. Constraints & Mandatory-Rule References

- Appendix ה **#23** — cryptographic locking of the emission-decay model pre-series;
  deviation in the decay formula voids the game.
- **#26/#27** — free natural language only; numeric-position protocol forbidden.
- **#54** — total tokens consumed reported in the end JSON (metering here, sending in the
  reporting PRD). Ch. 6/#25 — providers never influence movement (see PRD_strategy.md).
- Pheromone values 0.9 / 0.10 / 5×5 are **fixed status**: asserted at config load; any
  altered value is refused. Local-truth rule (#8): own field never shown to own reader.
- 150-line limit: if `belief.py` outgrows it, the scent-likelihood model splits into
  `domain/likelihood.py`; provider files are naturally small (one class each).

## 6. Alternatives Considered & Justification

- **Particle filter for belief** — rejected: an exact grid distribution is cheap and
  transparent; particles add variance with no benefit at 7×7-minimum scale.
- **`template` as primary provider** (book's recommended zero-token track) — considered;
  we chose `claude_api` (Haiku) for richer arena banter (ADR-3), retaining template as the
  unconditional fallback so worst case equals the book's recommended mode at zero tokens.
- **`claude_cli` as primary** — rejected: highest cost, subscription-bound; implemented
  for completeness only. **Structured-JSON hints** — forbidden outright (#27); hint
  parsing uses lightweight NL heuristics (direction/landmark lexicon), not a schema.
- **Learning trust per opponent across games** — deferred; the single-series
  multiplicative update meets the KPI and stays explainable.

## 7. Success Criteria & Test Scenarios

1. **Given** an agent at (3,3) on a fresh board, **when** it emits, **then** the field
   equals the 5×5 matrix centered at (3,3) exactly; **given** emission at corner (0,0),
   **then** the window clips to the in-bounds quadrant (no wraparound).
2. **Given** τ = 0.9 in a cell and no re-emission, **when** one full turn passes, **then**
   τ = 0.81 (= 0.9·0.9); after ~7 turns τ crosses half-peak (readability property).
3. **Given** repeated STAY on one cell, **then** τ stays within the [0, 0.9] invariant
   after clamping/saturation (fuzz test).
4. **Given** both peers' `model_lock_sha256` over identical configs, **then** digests
   match byte-for-byte; **given** a peer with ρ = 0.2, **then** digests differ and the
   series refuses to start (rule #23).
5. **Given** thief scent concentrated south-east ((1,4): 0.81, (1,3): 0.63, north 0.00)
   and the hint "I moved north", **when** `score_hint` runs, **then** expected ≈ 0.81,
   measured = 0.00, contradiction = True; trust drops; the belief argmax lands in the
   south-east concentration (worked example, rulebook §4.4).
6. **Given** a consistent truthful hint, **then** trust rises (bounded ≤ 1) and the hint
   likelihood weight grows accordingly.
7. **Given** an LLM answer of 22 words, **then** `validate_hint` truncates/regenerates to
   ≤ 15 words; **given** output containing "(4,2)" or "row 4 col 2", **then** rejected and
   replaced by a template sentence (no numeric position leaves the peer).
8. **Given** `claude_api` raising a 429/timeout, **then** the hint is produced by
   `template` in the same turn — the game continues (fallback chain, no crash).
9. **Given** `every_n_steps = 3`, **then** LLM calls occur only on steps 3, 6, 9, …;
   the meter total appears in the series report; **given** 90% budget use, **then** all
   remaining hints are template-produced.
10. **Given** `map_area = "Haifa"`, template hints include Haifa landmarks;
    **given** `map_area = ""`, generic landmarks.
11. **Edge:** barrier cells always show belief 0; belief renormalizes to Σ=1 after every
    update (property test); empty/duplicate hint → treated as no-hint (scent-only update).

## 8. Out of Scope

- Sealing the Intent flag into the SHA-256 commit and its audit (PRD_commit_reveal.md);
  this PRD only supplies `intent` and `hint` values to the packer.
- Transporting hints over MCP (PRD_p2p_mcp.md); heatmap rendering (PRD_gui_replay.md);
  emailing token totals (PRD_reporting_gatekeeper.md) — metering only here.
- Move selection from the belief map (PRD_strategy.md); opponent psychological profiling
  beyond the trust coefficient.
