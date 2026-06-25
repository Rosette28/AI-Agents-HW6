"""Phase 7 bonus inter-group competition ONLY — not part of the mandatory
submission. The partner-side half of the coordination protocol in
`docs/prd/bonus-inter-group.md`: whichever group did NOT run
`scripts/run_bonus_series.py` still needs to send the *same* result from
their own inbox automatically, not by hand-pasting it into an email
client — that's what this script is for.

It does no game-playing, no MCP/LLM calls at all — just loads the JSON
file the other group shared with you, validates it against the official
schema, and sends it via the Gmail API using *your own* OAuth credentials
(the same `GMAIL_CLIENT_SECRET_PATH`/`GMAIL_TOKEN_PATH` you already set up
for your own mandatory submission report — no new credential setup, and
nothing from the other group's `.env` is needed here at all).

Refuses to send unless the payload's `mutual_agreement` field is already
`true` — that field should only be set once you've independently
confirmed the totals match what you observed on your own server, per
`docs/prd/bonus-inter-group.md`.

Run:
    python scripts/send_bonus_report.py --payload-file path/to/shared_payload.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.loader import load_config  # noqa: E402
from src.reporting.bonus_schema import BonusSchemaError, validate_bonus_game_json  # noqa: E402
from src.reporting.gmail_sender import send_report  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-file", required=True,
                         help="Path to the JSON file the other group shared with you")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = _parse_args()
    config = load_config()

    payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    validate_bonus_game_json(payload)

    if not payload.get("mutual_agreement"):
        raise BonusSchemaError(
            "mutual_agreement is not true in this payload — confirm the totals match what you "
            "independently observed on your own server before sending. Do not send a payload you "
            "haven't verified yourself."
        )

    recipient = os.environ.get("REPORT_RECIPIENT_OVERRIDE") or config["reporting"]["recipient_email"]
    subject = (f"HW06 Cops and Thieves -- Inter-Group Bonus Game JSON Report "
               f"({payload['groups']['group_1']} vs {payload['groups']['group_2']})")
    response = send_report(payload, recipient, subject=subject)
    print(f"Bonus report emailed to {recipient} (message id {response['id']}).")


if __name__ == "__main__":
    main()
