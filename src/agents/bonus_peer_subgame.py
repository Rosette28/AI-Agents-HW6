"""Phase 7 bonus per-sub-game turn loop — split out of
`src.agents.bonus_peer` to keep both files under the 150-line limit.

Each side runs this independently, deciding only its own moves; capture is
checked from each side's own `report_location` calls on both servers
after every single move (whoever moved), matching the base game's
"position equality = Cop win regardless of who moved" rule.
"""

from src.agents.bonus_peer import act, client, positions, wait_for_opponent_move


async def run_subgame_as_peer(my_role: str, my_endpoint: dict, partner_endpoint: dict, llm_client,
                               grid_size: tuple, max_moves: int, max_barriers: int,
                               visibility_radius: int, my_start_pos: tuple, rng) -> dict:
    opponent_role = "thief" if my_role == "cop" else "cop"
    async with client(my_endpoint) as my_client, client(partner_endpoint) as partner_client:
        await my_client.call_tool("start_subgame", {"position": list(my_start_pos)})

        belief = None
        last_seen: dict | None = None
        transcript: list = []
        my_barriers: list = []
        barriers_remaining = max_barriers if my_role == "cop" else 0
        moves_taken = max_moves
        captured = False

        for round_number in range(1, max_moves + 1):
            print(f"    Round {round_number}/{max_moves}", end="\r", flush=True)
            if my_role == "cop":
                last_seen = await wait_for_opponent_move(my_client, last_seen)
                transcript.append({"agent": opponent_role, "message": last_seen["text"]})
                if await _captured(my_client, partner_client):
                    captured, moves_taken = True, round_number
                    break

            action, text, my_barriers, belief = await act(
                my_role, my_client, partner_client, llm_client, grid_size, max_moves,
                max_barriers, visibility_radius, belief, last_seen, barriers_remaining, my_barriers, rng,
            )
            if action["type"] == "place_barrier":
                barriers_remaining -= 1
            transcript.append({"agent": my_role, "action": action, "message": text})
            if await _captured(my_client, partner_client):
                captured, moves_taken = True, round_number
                break

            if my_role == "thief":
                last_seen = await wait_for_opponent_move(my_client, last_seen)
                transcript.append({"agent": opponent_role, "message": last_seen["text"]})
                if await _captured(my_client, partner_client):
                    captured, moves_taken = True, round_number
                    break

        my_pos, partner_pos = await positions(my_client, partner_client)
        cop_pos = my_pos if my_role == "cop" else partner_pos
        thief_pos = partner_pos if my_role == "cop" else my_pos
        # Barrier count is exact from whichever side played Cop this half (it
        # tracks its own placements directly); the Thief-side observer has no
        # tool to query the opponent's barrier count, so reports a
        # best-effort 0 here — informational only, doesn't affect scoring.
        barriers_placed = (max_barriers - barriers_remaining) if my_role == "cop" else 0
        return {
            "winner": "cop" if captured else "thief", "moves_taken": moves_taken,
            "final_cop_pos": cop_pos, "final_thief_pos": thief_pos,
            "barriers_placed": barriers_placed, "transcript": transcript,
        }


async def _captured(my_client, partner_client) -> bool:
    my_pos, partner_pos = await positions(my_client, partner_client)
    return my_pos == partner_pos
