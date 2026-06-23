"""Single sub-game turn loop: Thief moves first, then Cop, repeating until
capture or max_moves. Policies are plain callables so this module never
depends on an LLM or networking — Phase 1 wires it with scripted/heuristic
policies; Phase 2+ swaps in MCP-backed orchestrators with the same signature.
"""

from src.engine.board import Board

Policy = "Callable[[Board, str], dict]"  # callable(board, agent) -> action dict


def _apply_action(board: Board, agent: str, action: dict) -> dict:
    """Apply one action dict for `agent` and return the engine's result."""
    if action["type"] == "move":
        return board.move(agent, action["direction"])
    if action["type"] == "place_barrier" and agent == "cop":
        return board.place_barrier()
    return {"accepted": False, "reason": "illegal_action_for_agent"}


def run_subgame(board: Board, max_moves: int, thief_policy, cop_policy) -> dict:
    """Run one sub-game to completion.

    Returns a result dict: winner ('cop'|'thief'), moves_taken, and the
    final board state (positions, barriers placed).
    """
    transcript = []
    for move_number in range(1, max_moves + 1):
        for agent, policy in (("thief", thief_policy), ("cop", cop_policy)):
            pos = board.thief_pos if agent == "thief" else board.cop_pos
            has_move = bool(board.legal_moves(pos))
            can_act = has_move or agent == "cop"
            if not can_act:
                transcript.append({"agent": agent, "action": "skip_no_legal_moves"})
                continue

            action = policy(board, agent)
            result = _apply_action(board, agent, action)
            transcript.append({"agent": agent, "action": action, "result": result})

            if board.is_captured():
                return {
                    "winner": "cop",
                    "moves_taken": move_number,
                    "final_cop_pos": board.cop_pos,
                    "final_thief_pos": board.thief_pos,
                    "barriers_placed": board.barriers_placed,
                    "transcript": transcript,
                }

    return {
        "winner": "thief",
        "moves_taken": max_moves,
        "final_cop_pos": board.cop_pos,
        "final_thief_pos": board.thief_pos,
        "barriers_placed": board.barriers_placed,
        "transcript": transcript,
    }
