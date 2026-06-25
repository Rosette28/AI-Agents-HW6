"""Phase 7 bonus inter-group competition ONLY — not part of the mandatory
submission. Runs one attempt of the swapped-role 3+3 bonus series against
a partner group's deployed servers. Split out of
`scripts/run_bonus_series.py` (which retries this whole function on an
exact-tie result) to keep that CLI file under the project's 150-line
limit, and to make this logic unit-testable without going through argparse.

Each half is played via `src.agents.bonus_peer_half.run_bonus_half_as_peer`
— our own orchestrator decides only *our own* agent's moves each half,
using our own strategy/LLM; the partner group runs this exact same module
independently to decide theirs. See `src.agents.bonus_peer`'s module
docstring for why a single shared orchestrator (the original design here)
was wrong — it never actually exercised the partner's own strategy.
"""

import os

from src.agents.bonus_peer_half import run_bonus_half_as_peer
from src.agents.llm_client import build_llm_client
from src.reporting.bonus_report import build_bonus_game_json
from src.reporting.bonus_scoring import compute_bonus_claim


def _endpoint(url: str, token: str | None) -> dict | None:
    return {"url": url, "token": token} if url else None


async def run_one_bonus_attempt(
    our_role_half1: str, partner_cop_url: str, partner_cop_token: str,
    partner_thief_url: str, partner_thief_token: str,
    our_team: dict, partner_team: dict, config: dict, series_seed,
) -> dict:
    """Plays both swapped-role halves once (each as our own independent
    peer process — see module docstring) and returns the assembled
    Inter-Group Bonus Game JSON (`bonus_claim` filled in,
    `mutual_agreement` left unset — that's the caller's job, once the
    partner group has confirmed the result matches their own observation).

    `series_seed` must be agreed with the partner group ahead of time —
    both sides need the *same* value so each independently derives the
    same starting positions per sub-game (`bonus_peer_half`).
    """
    grid_size = tuple(config["board"]["grid_size"])
    llm_client = build_llm_client(config)
    sub_games_per_half = config["bonus"]["sub_games_per_half"]

    our_cop = _endpoint(config["mcp"]["cop_mcp_url"], os.environ.get("COP_MCP_AUTH_TOKEN"))
    our_thief = _endpoint(config["mcp"]["thief_mcp_url"], os.environ.get("THIEF_MCP_AUTH_TOKEN"))
    partner_cop = {"url": partner_cop_url, "token": partner_cop_token}
    partner_thief = {"url": partner_thief_url, "token": partner_thief_token}
    our_role_half2 = "thief" if our_role_half1 == "cop" else "cop"

    half_kwargs = dict(
        llm_client=llm_client, grid_size=grid_size, max_moves=config["game"]["max_moves"],
        max_barriers=config["game"]["max_barriers"], scoring=config["scoring"],
        visibility_radius=config["observation"]["visibility_radius"], num_sub_games=sub_games_per_half,
        series_seed=series_seed,
    )
    print(f"Half 1 (we play {our_role_half1}): {sub_games_per_half} sub-games...")
    half_1 = await run_bonus_half_as_peer(
        our_role_half1, our_cop if our_role_half1 == "cop" else our_thief,
        partner_thief if our_role_half1 == "cop" else partner_cop, half_index=1, **half_kwargs,
    )
    print(f"Half 1 totals: {half_1['totals']}")

    print(f"Half 2 (we play {our_role_half2}, roles swapped):")
    half_2 = await run_bonus_half_as_peer(
        our_role_half2, our_cop if our_role_half2 == "cop" else our_thief,
        partner_thief if our_role_half2 == "cop" else partner_cop, half_index=2, **half_kwargs,
    )
    print(f"Half 2 totals: {half_2['totals']}")

    payload = build_bonus_game_json(our_team, partner_team, half_1, half_2, our_role_half1, config["timezone"])
    payload["bonus_claim"] = compute_bonus_claim(payload["totals_by_group"])
    return payload
