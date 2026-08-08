"""Check an opponent's ``game.json`` against ours before the match, not during.

A disagreeing signed term refuses the handshake at kickoff with both teams
waiting; every one of those values is readable from the two config files the
night before. Point this at the file the opponent sent and it names the
disagreements, or says the terms would pass.

    uv run python scripts/preflight.py --their-config ~/Downloads/game.json

Add ``--role`` (our role in sub-game 1) to have the role reminder printed the
right way round. Nothing here is written to the repo and no opponent value is
stored - read the report, fix the config, delete the file.

Exit status is 1 when a blocker is found, so it can gate a launch script.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from police_thief.shared.config import ConfigManager  # noqa: E402
from police_thief.shared.config_io import ConfigError, read_json  # noqa: E402
from police_thief.shared.interop import negotiate_extras, terms_from_contract  # noqa: E402
from police_thief.shared.preflight import (  # noqa: E402
    compare_signed_terms,
    report_lines,
    terms_from_raw,
    would_handshake,
)


def parse_args() -> argparse.Namespace:
    """Command-line surface: the opponent's file and which role we open as."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--their-config", required=True,
                        help="path to the game.json the opponent sent")
    parser.add_argument("--role", default="police", choices=["police", "thief"],
                        help="our role in sub-game 1 (default: police)")
    return parser.parse_args()


def main() -> int:
    """Compare both configs and print the verdict; 1 when a blocker is found."""
    args = parse_args()
    ours = terms_from_contract(ConfigManager.load(args.role).contract)
    try:
        theirs = terms_from_raw(read_json(args.their_config))
    except ConfigError as error:
        print(f"BLOCKER - their config does not load under our contract rules:\n  {error}")
        print("  Our peer would fail to start on this file; ask them for the missing key.")
        return 1

    differences = compare_signed_terms(ours, theirs)
    for line in report_lines(differences, negotiate_extras(args.role, 1), args.role):
        print(line)
    return 0 if would_handshake(differences) else 1


if __name__ == "__main__":
    raise SystemExit(main())
