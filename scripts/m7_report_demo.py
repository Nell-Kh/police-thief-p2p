"""M7 end-to-end shell run: play, write the lifecycle files, mail the report.

Plays one local mini-game, assembles all four lifecycle JSON files under
``results/``, and pushes the result report through the full Gmail pipeline -
Gatekeeper gates included. With a real ``credentials.json`` beside the repo
(Appendix A) the report lands in Gmail Drafts; without one, a local stub
service receives the identical bytes, so the whole pipeline is still
exercised end-to-end. Run: ``uv run python scripts/m7_report_demo.py``.
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from police_thief.constants import ROLE_POLICE, ROLE_THIEF
from police_thief.infra.email.reports import (
    config_file_name,
    config_payload,
    declaration_file_name,
    declaration_payload,
    result_file_name,
    result_payload,
    write_lifecycle_file,
)
from police_thief.infra.email.sender import configured_sender
from police_thief.services.runtime import runner_from_config
from police_thief.shared.config import ConfigManager
from police_thief.shared.config_io import sha256_of
from police_thief.shared.sysinfo import hardware_spec


def git_head() -> str:
    """The exact commit playing this game (rulebook ch. 5.5)."""
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return out.stdout.strip() or "uncommitted"


def stub_service() -> SimpleNamespace:
    """A Gmail double for machines without credentials - same call shape."""
    def request(kind: str) -> SimpleNamespace:
        return SimpleNamespace(execute=lambda: print(f"  [stub gmail] {kind} accepted"))

    # ``userId`` mirrors the real Gmail API keyword, hence the noqa.
    drafts = SimpleNamespace(create=lambda userId, body: request("draft"))  # noqa: N803
    messages = SimpleNamespace(send=lambda userId, body: request("send"))  # noqa: N803
    return SimpleNamespace(users=lambda: SimpleNamespace(drafts=lambda: drafts,
                                                         messages=lambda: messages))


def real_or_stub_service() -> SimpleNamespace:
    """Real Gmail when Appendix A setup exists here; otherwise the stub."""
    if Path("credentials.json").exists():
        from police_thief.infra.email.oauth import build_gmail_service, load_credentials

        return build_gmail_service(load_credentials())
    print("no credentials.json here - using the stub service (pipeline unchanged)")
    return stub_service()


def main() -> None:
    """One counted mini-game, four lifecycle files, one gated report."""
    config = ConfigManager.load(ROLE_POLICE)
    runner = runner_from_config(config)
    state = runner.play()
    outcome = state.outcome
    print(f"mini-game over at step {state.step}: {outcome.event} - {outcome.reason}")

    now = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    game_id = f"demo_{now[:10]}"
    game_uid = sha256_of({"game_id": game_id, "started_at": now})[:16]
    teams = {"A": {"name": "nell", "members": ["nell"]}, "B": {"name": "self-play", "members": []}}
    repos = {"A_police": "https://github.com/<user>/police-agent",
             "A_thief": "https://github.com/<user>/thief-agent",
             "B_police": "(self-play)", "B_thief": "(self-play)"}

    results_dir = Path("results")
    declaration = declaration_payload(
        game_uid=game_uid, game_id=game_id, teams=teams, repositories=repos,
        mcp_servers={"police": "http://127.0.0.1:8801", "thief": "http://127.0.0.1:8802"},
        hardware=hardware_spec(), llm_model="claude-haiku",
        token_budget=config.contract.network.token_budget_per_series,
        started_at=now, ended_at=now,
    )
    mini = [{"number": 1, "github_commit": git_head(),
             "police_points": outcome.points_for(ROLE_POLICE),
             "thief_points": outcome.points_for(ROLE_THIEF), "event": outcome.event}]
    result = result_payload(
        game_uid=game_uid, game_id=game_id, teams=teams, repositories=repos,
        mini_games=mini, tokens_total=0,
        agreement={"ours": config.config_sha256, "theirs": config.config_sha256},
    )
    for name, payload in [
        (declaration_file_name(game_id), declaration),
        (config_file_name(game_id, 1), config_payload(game_uid, game_id, 1, config.raw_contract)),
        (result_file_name(game_id), result),
    ]:
        print(f"  wrote {write_lifecycle_file(results_dir, name, payload)}")

    sender = configured_sender(config, real_or_stub_service())
    status = sender.send_report(
        subject=f"Police-Thief result {game_id}",
        body="Automated game report attached as machine-readable JSON.",
        attachment_name=result_file_name(game_id), payload=result,
    )
    print(f"report → {sender.recipient} [{sender.mode}]: {status}")
    print(f"gatekeeper log: {sender._gatekeeper.log}")  # noqa: SLF001 - demo introspection


if __name__ == "__main__":
    main()
