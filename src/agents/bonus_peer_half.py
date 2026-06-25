"""Phase 7 bonus per-half loop: plays `num_sub_games` sub-games with a
fixed Cop/Thief role assignment (one "half" of the swapped-role 3+3
series), accumulating totals in the exact same shape
`src.agents.orchestrator_series.run_series_via_mcp` already returns — so
`src.agents.bonus_runner`/`src.reporting.bonus_report` didn't need to
change at all when this peer-based half-runner replaced the old (flawed)
single-orchestrator one. See `src.agents.bonus_peer`'s module docstring.
"""

import random

from src.agents.bonus_peer_subgame import run_subgame_as_peer
from src.agents.orchestrator_series import score_subgame
from src.engine.start_positions import random_start_positions


async def run_bonus_half_as_peer(
    my_role: str, my_endpoint: dict, partner_endpoint: dict, llm_client,
    grid_size: tuple, max_moves: int, max_barriers: int, scoring: dict,
    visibility_radius: int, num_sub_games: int, series_seed, half_index: int,
) -> dict:
    """`series_seed` + `half_index` + the sub-game index together seed a
    `random.Random` both sides construct identically and independently —
    so both sides pick the *same* (cop_pos, thief_pos) pair for each
    sub-game without any network coordination, guaranteeing the two
    agents never collide on the same starting cell.
    """
    cop_total = thief_total = 0
    sub_games = []
    for sub_game_index in range(1, num_sub_games + 1):
        # random.Random only accepts None/int/float/str/bytes/bytearray —
        # str() of the tuple is deterministic and reproducible across
        # independent processes, which is all that's needed here.
        seed = str((series_seed, half_index, sub_game_index))
        cop_pos, thief_pos = random_start_positions(grid_size, rng=random.Random(seed))
        my_start_pos = cop_pos if my_role == "cop" else thief_pos

        result = await run_subgame_as_peer(
            my_role, my_endpoint, partner_endpoint, llm_client, grid_size, max_moves,
            max_barriers, visibility_radius, my_start_pos, random.Random(seed),
        )
        cop_points, thief_points = score_subgame(result["winner"], scoring)
        result["cop_points"], result["thief_points"] = cop_points, thief_points
        cop_total += cop_points
        thief_total += thief_points
        sub_games.append(result)

    return {"totals": {"cop": cop_total, "thief": thief_total}, "sub_games": sub_games}
