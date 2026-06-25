"""Phase 7 bonus inter-group competition ONLY — not part of the mandatory
submission. See `docs/prd/bonus-inter-group.md` for the full coordination
protocol; short version:

**BOTH groups run this exact same script**, each pointed at their own two
servers (their role each half) and the partner's two servers (the
opposite role) — not just one side. Each side's own copy decides only its
own agent's moves using its own strategy/LLM (`src.agents.bonus_peer`);
the two independent processes stay synchronized via tools every
compliant server already exposes (`report_location`, message relay).
Both sides therefore independently arrive at their own observation of the
same shared real game, which is what should be compared (not "shared")
before either one sends.

Both sides must agree ahead of time on:
  - `--series-seed` (any string/int) — both sides need the *same* value so
    each independently derives the same starting positions per sub-game.
  - `--our-role-half1` — exact inverses of each other (if we say `cop`,
    the partner must say `thief`).
  - `config.yaml: bonus.max_draw_retries` — should match on both sides,
    so a retry on a tied result stays in lockstep (each side's own
    `start_subgame` call resets that side's inbox/state cleanly for the
    next attempt, so no extra protocol is needed beyond this).

If the result is an exact tie (5/5 bonus points, lose-lose for both
groups) it's retried automatically, up to
`config.yaml: bonus.max_draw_retries` times. If still tied after the last
attempt, `config.yaml: bonus.send_email_on_draw_after_max_retries`
decides whether to send that tied result anyway or stop without sending —
agree this with the partner group and set it explicitly; the default
(`false`) is the safer "don't send" choice.

Prerequisites: ANTHROPIC_API_KEY in .env; our own COP_MCP_AUTH_TOKEN/
THIEF_MCP_AUTH_TOKEN and config.yaml: mcp.{cop,thief}_mcp_url already
deployed and working (i.e. scripts/run_llm_demo.py works first); the
partner group's four pieces of info (their Cop/Thief URLs + tokens) and
team metadata, passed as CLI arguments below — never hardcoded, and never
committed (they're per-competition, not a fixed deployment setting). The
partner's server must expose the same tool contract this script calls
(`report_location`, `receive_message`, `sync_barriers`, `choose_action`,
`start_subgame`, `read_message`) — confirm this before a real run.

Run, e.g.:
    python scripts/run_bonus_series.py \\
        --partner-name "Team-Beta" \\
        --partner-github-repo https://github.com/team-beta/marl-copthief \\
        --partner-cop-url https://cop-mcp-beta.example.com/mcp --partner-cop-token TOKEN_THEY_GAVE_US \\
        --partner-thief-url https://thief-mcp-beta.example.com/mcp --partner-thief-token TOKEN_THEY_GAVE_US \\
        --our-role-half1 cop --series-seed bonus-2026-06-25
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agents.bonus_runner import run_one_bonus_attempt  # noqa: E402
from src.config.loader import load_config  # noqa: E402
from src.reporting.bonus_schema import validate_bonus_game_json  # noqa: E402
from src.reporting.bonus_scoring import is_draw  # noqa: E402
from src.reporting.gmail_sender import send_report  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--partner-name", required=True)
    parser.add_argument("--partner-students", default="", help="comma-separated")
    parser.add_argument("--partner-github-repo", required=True)
    parser.add_argument("--partner-cop-url", required=True)
    parser.add_argument("--partner-cop-token", required=True)
    parser.add_argument("--partner-thief-url", required=True)
    parser.add_argument("--partner-thief-token", required=True)
    parser.add_argument("--our-role-half1", choices=["cop", "thief"], default="cop")
    parser.add_argument("--series-seed", required=True,
                         help="Any string/int, AGREED WITH THE PARTNER GROUP — both sides must pass the same value")
    parser.add_argument("--send", action="store_true",
                         help="Actually email our copy (config.yaml: bonus.send_on_completion must also be true)")
    return parser.parse_args()


async def main() -> None:
    load_dotenv()
    args = _parse_args()
    config = load_config()
    our_team = {
        "name": config["group"]["group_name"], "students": config["group"]["students"],
        "github_repo": config["group"]["github_repo"],
        "cop_mcp_url": config["mcp"]["cop_mcp_url"], "thief_mcp_url": config["mcp"]["thief_mcp_url"],
    }
    partner_team = {
        "name": args.partner_name,
        "students": [s.strip() for s in args.partner_students.split(",") if s.strip()],
        "github_repo": args.partner_github_repo,
        "cop_mcp_url": args.partner_cop_url, "thief_mcp_url": args.partner_thief_url,
    }

    max_attempts = config["bonus"]["max_draw_retries"]
    payload = None
    for attempt in range(1, max_attempts + 1):
        print(f"\n=== Bonus series attempt {attempt}/{max_attempts} ===")
        payload = await run_one_bonus_attempt(
            args.our_role_half1, args.partner_cop_url, args.partner_cop_token,
            args.partner_thief_url, args.partner_thief_token, our_team, partner_team, config,
            series_seed=(args.series_seed, attempt),
        )
        print(f"Totals by group: {payload['totals_by_group']}  |  Bonus claim: {payload['bonus_claim']}")
        if not is_draw(payload["totals_by_group"]):
            break
        print("Exact tie (5/5, lose-lose for both groups) — retrying the whole series." if attempt < max_attempts
              else "Still a tie after the last attempt.")

    if is_draw(payload["totals_by_group"]) and not config["bonus"]["send_email_on_draw_after_max_retries"]:
        print(f"\nTied after {max_attempts} attempt(s) and "
              "config.yaml: bonus.send_email_on_draw_after_max_retries is false — not sending. "
              "Agree this with the partner group, then set that flag explicitly if you want a tied "
              "result sent instead of re-attempted later.")
        return

    payload["mutual_agreement"] = True  # only true once compared against the partner's own independent run
    validate_bonus_game_json(payload)
    print("\nFull payload (compare totals_by_group/bonus_claim/sub_games against the partner "
          "group's own independently-run copy of this same script before either side sends):")
    print(payload)

    if not (args.send and config["bonus"]["send_on_completion"]):
        print("\nNot sending (pass --send and set config.yaml: bonus.send_on_completion: true "
              "once the partner group has confirmed the totals above match their own observation).")
        return

    recipient = os.environ.get("REPORT_RECIPIENT_OVERRIDE") or config["reporting"]["recipient_email"]
    subject = f"HW06 Cops and Thieves -- Inter-Group Bonus Game JSON Report ({payload['groups']['group_1']} vs {payload['groups']['group_2']})"
    response = send_report(payload, recipient, subject=subject)
    print(f"Bonus report emailed to {recipient} (message id {response['id']}).")


if __name__ == "__main__":
    asyncio.run(main())
