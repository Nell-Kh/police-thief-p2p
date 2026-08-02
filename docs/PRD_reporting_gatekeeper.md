# PRD — Gmail Reporting Automation, Gatekeeper and Lifecycle Files

**Project:** police-thief-p2p | **Version:** 1.00 | **Status:** awaiting approval
**Parent docs:** docs/PRD.md §3.9, docs/PLAN.md §1.4/§4 | **Rulebook:** ch. 9, Appendix א, Appendix ו.2–ו.3, Appendix ה
**Dev priority:** Stage 7 (rulebook ch. 10) — the reporting shell, built last.

---

## 1. Purpose & Theoretical Background

League play ends every legal game with a **mandatory automatic report** — no human touches the
keyboard, and **both** teams each send their own report **separately**. Automation is blessing
and trap: buggy code holds the key to a live Gmail account, and Gmail is a quota-managed
real-world resource — one call too many and Google returns HTTP 429 or suspends the account.

The protective layer is the **Gatekeeper** pattern (guidelines ch. 5; rulebook §9.3.1), a
reliability pattern in the Watchdog/Deadline-Tracker family: **all external API calls pass
through one central gate** of three cumulative mechanisms — a **Quota Manager** (daily cap;
last line before suspension), a **Token Bucket rate limiter** (mandatory, #28) and a **DOS
detector** (mandatory, #29; backpressure + circuit breaker). Terminology: here "token" always
means a *rate token* — never an LLM token nor an OAuth token. The token-bucket update rule
(rulebook §9.3.2, verbatim): `tokens ← min(C, tokens + r·Δt)` , `allow ⟺ tokens ≥ 1` — C caps
the burst, r caps the long-run average (which must stay below Google's quota).

Authorization uses **OAuth 2.0** with the single least-privilege scope
`https://www.googleapis.com/auth/gmail.send`: a short-lived **access token** rides on every
API call; a long-lived **refresh token** (never sent to the mail API) mints new access tokens,
giving the agent months of autonomy with no manual step.

## 2. Binding Parameters Used

| Parameter (Appendix ו) | Config key | Value | Status |
|---|---|---|---|
| Requests per minute [בקשות לדקה] | `rate_limiter_gatekeeper.requests_per_minute` | 30 | Minimum |
| Concurrent requests [בקשות מקבילות] | `rate_limiter_gatekeeper.concurrent_requests` | 2 | Minimum |
| Delay after error [השהיה לאחר שגיאה] | `rate_limiter_gatekeeper.retry_backoff_sec` | 5 s | Minimum |
| Retries [ניסיונות חוזרים] | `rate_limiter_gatekeeper.max_retries` | 3 | Minimum |
| Queue depth [עומק התור] | `rate_limiter_gatekeeper.queue_depth` | 100 | Minimum |
| Agent-reports address [כתובת דיווחי הסוכן] | private TOML `[email] recipient` | `rmisegal+uoh26finalgame@gmail.com` | Fixed (only binding address) |
| Min games to pass [מינימום משחקים למעבר] | `network_and_league.min_games_to_pass` | 2 | Fixed |
| Max games per team [מספר המשחקים המרבי] | `network_and_league.max_games_per_team` | 10 | Fixed |
| Diversity reward [תגמול גיוון] | `network_and_league.diversity_reward` | 10 | Fixed |
| Number of mini-games [מספר המשחקונים] | `network_and_league.num_games` | 6 | Fixed |
| Token estimate per series [אומדן טוקנים לסדרה] | `network_and_league.token_budget_per_series` | ~200000 | Negotiation |
| Lifecycle file names [קובץ ההצהרה/התצורה/היומן/התוצאות] | derived from `game_id` | see §3 FR-1 | Fixed naming |

Rate limits are loaded from configuration — `config/rate_limits.json` mirroring the shared
`rate_limiter_gatekeeper` section — and are **never hardcoded** (Appendix ב names
`rate_limits.json` as the rate-limiter JSON; values may only be tightened, never eased below
the minima). Email mode is a private TOML choice: `[email] mode = "draft" | "send"`.

## 3. Functional Requirements

- **FR-1 Lifecycle files (`infra/email/reports.py` + `domain/logbook.py`).** Produce four JSON
  files sharing one `game_uid`, names derived from `game_id`:
  `declaration_<game_id>.json` (Step-0 constants: teams, members, both repos, hardware, LLM,
  token cap, times, signature), `config_<game_id>_g<NN>.json` (per-mini-game locked config —
  also committed to GitHub, Appendix ו.2 #3–#4), `log_<game_id>_g<NN>.json` (per-step
  commit-reveal log), `result_<game_id>.json` (per-mini-game scores + cumulative result — the
  binding emailed report). Files from different games can never mix.
- **FR-2 Results content.** `result_<game_id>.json` includes: both teams' identities, **all
  four GitHub links** (team A cop+thief, team B cop+thief), FastMCP server addresses,
  `github_commit` per mini-game, signed hardware declarations, timestamps, SHA-256-backed
  mutual-agreement confirmations, per-mini-game and total scores, and **total LLM tokens
  consumed** (rule #54).
- **FR-3 Automatic dispatch.** At the end of every legal game, after the mutual audit (#36) and
  result agreement (#35), our peer sends the report **by itself** — no human intervention — as
  a **machine-readable JSON email attachment** (plaintext body reports are rejected, #33/#34)
  to `rmisegal+uoh26finalgame@gmail.com`, the only binding address (#51), hard-set as the
  default recipient in code config for both agents.
- **FR-4 OAuth setup (`infra/email/oauth.py`).** Follow Appendix א's five steps in order:
  (1) Cloud Console project + enable Gmail API; (2) OAuth consent screen + Test Users;
  (3) scope restricted to `gmail.send` **only** (#30 — never request read/modify);
  (4) Desktop-app OAuth Client ID → `credentials.json`; (5) first authorization flow →
  `token.json` (access + refresh tokens). Code loads `token.json` when present, runs
  `InstalledAppFlow` once otherwise, and auto-refreshes access tokens thereafter.
- **FR-5 Secrets hygiene.** `credentials.json` and `token.json` are git-ignored **before the
  first commit** (#39/#40); `.gitignore` at repo root lists both plus `.env`; a leaked secret
  is exposed forever → rotate in the console.
- **FR-6 Central Gatekeeper (`shared/gatekeeper.py`).** Every external API call (Gmail, and
  cloud LLM calls from `infra/llm/`) passes the three gates in order:
  Quota Manager → Token Bucket → DOS Detector → provider. Fail-fast at the earliest gate.
- **FR-7 Quota Manager.** Daily operation counter with a configured cap; when exhausted, no
  request leaves the process until the day rolls over.
- **FR-8 Token Bucket (`shared/bucket.py`).** Implements the update rule above with continuous
  refill on monotonic time; `allow(cost=1.0)` spends a token or refuses; r and C derive from
  `requests_per_minute` (r = rpm/60) and burst config; mandatory (#28).
- **FR-9 DOS detector.** Monitors the send pattern (sends per sliding window far above normal
  game cadence, or repeats of an identical payload); on anomaly it **locks the whole pipeline**
  (LOCKED, circuit open) — sacrificing a report to save the account (#29). Unlock is explicit
  (operator/config), never automatic mid-anomaly.
- **FR-10 Overflow queue.** A request refused by any gate is enqueued in a FIFO of
  `queue_depth` (100) and retried when tokens refill — **never rejected outright, never a
  crash**; beyond depth, oldest-drop with a logged warning (no exception to the caller).
- **FR-11 429 respect.** On HTTP 429 (or 5xx), back off `retry_backoff_sec` (5 s, exponential
  ×2 per attempt) up to `max_retries` (3); never hammer-resend. Concurrency capped at
  `concurrent_requests` (2).
- **FR-12 Game-count declaration.** At every game start our peer declares exactly how many
  counted games it has already played (feeds diversity-incentive weighting); a false
  declaration disqualifies (#37/#38). Count persisted in `data/` and cross-checkable against
  reports already emailed.
- **FR-13 One counted game per opponent.** Enforced at negotiation: warm-ups allowed and
  flagged `counted=false` (no report obligation); a counted rematch against a sealed pairing
  is refused (#52).
- **FR-14 Draft/send modes (`infra/email/sender.py`).** Private TOML `[email] mode`: `draft`
  creates a Gmail draft (development default — verifiable without spamming the lecturer);
  `send` transmits for real league games. Both paths go through the Gatekeeper.

## 4. Input/Output Contracts

```python
# shared/bucket.py
class TokenBucket:
    def __init__(capacity: float, refill_rate: float) -> None   # from rate_limits config
    def allow(cost: float = 1.0) -> bool                        # refill then spend-or-refuse

# shared/gatekeeper.py
@dataclass GateVerdict: allowed: bool; gate: str                # "quota"|"bucket"|"dos"|"open"
class Gatekeeper:
    def __init__(limits: RateLimits, clock=time.monotonic) -> None
    def submit(request: ApiRequest) -> GateVerdict              # enqueue on refusal (FIFO 100)
    def pump() -> list[ApiRequest]                              # dequeue what is now allowed
    def locked() -> bool                                        # DOS circuit state
class RateLimits:                                               # parsed, never hardcoded
    requests_per_minute: int; concurrent_requests: int
    retry_backoff_sec: int; max_retries: int; queue_depth: int

# infra/email/oauth.py
def get_service(credentials_path: Path, token_path: Path) -> GmailService
    # scope == ["https://www.googleapis.com/auth/gmail.send"] only

# infra/email/sender.py
def build_message(to_addr: str, subject: str, body: str,
                  attachments: list[Path]) -> dict              # base64url raw MIME
def dispatch(service, message: dict, mode: str,
             gatekeeper: Gatekeeper) -> SendResult              # mode: "draft"|"send"
    # SendResult: ok: bool; attempts: int; backoff_used_sec: float; gate: str

# infra/email/reports.py
def build_result_report(game: GameSummary) -> dict              # schema of result_<game_id>.json
def lifecycle_paths(game_id: str, nn: int) -> LifecyclePaths    # the four derived file names
def send_end_of_game_report(game_id: str, cfg: EmailConfig,
                            gatekeeper: Gatekeeper) -> SendResult
    # attaches result_<game_id>.json (+ declaration/config/log files), JSON attachment only
```

Retry/backoff policy is data-driven from `RateLimits`; `dispatch` sleeps
`retry_backoff_sec * 2**(attempt-1)` between attempts on 429/5xx and gives up after
`max_retries`, leaving the message in the FIFO queue for a later pump.

## 5. Constraints & Mandatory-Rule References (Appendix ה)

- **#28** Token-bucket rate limiter for Gmail reporting — mandatory (prevents 429 paralysis).
- **#29** DOS detector locking the interface — mandatory (protects the reporting account).
- **#30** Send-only Gmail scope (`gmail.send`); wider scope disqualifies (Appendix א step 3).
- **#32/#33/#34** Automatic reporting; standard JSON attachment; free-text reports refused —
  a non-JSON report forfeits the round's points.
- **#35** Result agreed with the opponent; **each team sends separately**; missing report ⇒ no
  points for that side even if it won; contradictory reports ⇒ disqualification, 0 for both.
- **#36** Comprehensive mutual log audit before agreeing the shared result JSON.
- **#37/#38** Precise game-count declaration at every game start; lying disqualifies.
- **#39/#40** No secrets in repo; `credentials.json`/`token.json` git-ignored pre-first-commit.
- **#51** Reports go only to `rmisegal+uoh26finalgame@gmail.com`.
- **#52** One counted game per opponent; warm-ups permitted.
- **#54** Total tokens consumed reported in the end JSON.
- **#31** League bounds: ≥ 2 games vs. different teams (`min_games_to_pass`), ≤ 10
  (`max_games_per_team`).
- Appendix ו.2: per-game config uniquely named and committed to GitHub; per-game email carries
  the `github_commit`. Guidelines: zero hardcoding; ≤ 150 code lines/file; coverage ≥ 85%
  (this subsystem is fully covered — no GUI here).

## 6. Alternatives Considered & Justification

- **SMTP with app password vs. Gmail API + OAuth 2.0** — rejected: Appendix א mandates the
  OAuth flow; raw passwords in code violate the security model and rule #30's spirit.
- **Broad scope (`gmail.modify` / `mail.google.com`)** — rejected: least privilege (#30); a
  stolen send-only token is a nearly harmless tool.
- **Reject-on-limit vs. FIFO overflow queue** — queue chosen: a dropped end-of-game report
  costs league points (#35); queue + pump guarantees eventual delivery. Depth 100 per minimum.
- **Immediate retry on 429 vs. backoff** — backoff mandated by the "iron rules" box; the
  exponential factor over the 5 s floor is our tightening (minima may only be raised).
- **Gatekeeper only for Gmail vs. for all external APIs** — all external calls (Gmail + cloud
  LLM) pass the gate: the DOS detector is only meaningful if nothing bypasses it.
- **Auto-unlock after DOS lock** — rejected: an anomaly signals a code bug; automatic unlock
  would resume the flood. Explicit operator reset required.

## 7. Success Criteria & Test Scenarios

- **T-1 Bucket math.** Given C=5, r=0.5, an empty bucket and Δt=2 s, when `allow()` is called,
  then tokens = min(5, 0+1) = 1 ⇒ allowed once, refused immediately after (fake clock).
- **T-2 Burst cap.** Given a full bucket C=5, when 7 requests arrive at once, then exactly 5
  pass and 2 are queued, none rejected, none crash.
- **T-3 Quota gate.** Given the daily quota exhausted, when a report is submitted, then verdict
  gate == "quota", nothing reaches the bucket, and the request sits in the queue for tomorrow.
- **T-4 DOS lock.** Given 50 identical sends within one window (simulated infinite loop), when
  the detector evaluates, then `locked()` is True, all later submits return gate == "dos", and
  no call reaches the (mocked) Gmail service; unlock only via explicit reset.
- **T-5 429 respect + exhaustion.** Given a mocked service returning 429 twice then 200, when
  `dispatch` runs, then it sleeps 5 s and 10 s (patched sleep) and succeeds on attempt 3; given
  429 four times with max_retries=3, it stops, returns ok=False, and the message stays queued
  (no crash, no hammer-resend).
- **T-6 Attachment format.** Given a finished game, when the report is built, then the email
  carries `result_<game_id>.json` as a JSON **attachment** (valid, parseable), including all
  four GitHub links, `github_commit` per mini-game, and total tokens consumed; grading data is
  never plaintext-only.
- **T-7 Address lock.** Given any config omitting a recipient, when the sender resolves the
  destination, then it is `rmisegal+uoh26finalgame@gmail.com`; overriding it in league mode
  fails validation.
- **T-8 Lifecycle naming.** Given `game_id="X7"` and mini-game 3, when `lifecycle_paths` runs,
  then names are `declaration_X7.json`, `config_X7_g03.json`, `log_X7_g03.json`,
  `result_X7.json`, all embedding the same `game_uid`.
- **T-9 Game count.** Given 2 counted games already reported, when a new game starts, then the
  declaration says 2; a counted rematch against a sealed pairing is refused (warm-ups allowed,
  flagged non-counted).
- **T-10 Draft mode.** Given `[email] mode="draft"`, when dispatching, then the Gmail drafts
  endpoint is called and nothing is sent; `mode="send"` hits the send endpoint — both gated.
- **T-11 Secrets gate.** Repo check: `.gitignore` contains `credentials.json`, `token.json`,
  `.env`; a test asserts none of these paths are tracked by git.

## 8. File Split for the 150-Line Rule

`shared/bucket.py` (TokenBucket only), `shared/gatekeeper.py` (quota + DOS + queue + gate
orchestration), `infra/email/oauth.py` (scope, credential/token loading, refresh),
`infra/email/sender.py` (MIME build, draft/send dispatch, backoff), `infra/email/reports.py`
(lifecycle schemas, report assembly, end-of-game entry point). If `gatekeeper.py` outgrows 150
lines, split `shared/quota.py` (Quota Manager) and `shared/dos.py` (detector); if `reports.py`
outgrows it, split `reports_schema.py` (dataclasses) from `reports_send.py` (assembly + send).

## 9. Out of Scope

- Content of the game log and the audit that precedes result agreement (PRD_commit_reveal.md).
- Step-0 hardware collection and signing (PRD_commit_reveal.md; reports only embed its output).
- LLM token *budgeting* strategy (PRD_scent_language.md) — this PRD only reports the totals.
- The opponent's report — each side reports separately; we never send on their behalf (#35).
- Receiving/reading email (send-only scope), inbound webhooks, non-Gmail providers.
- League scheduling/matchmaking UI; Moodle submission mechanics (Appendix ג / TODO M8).
