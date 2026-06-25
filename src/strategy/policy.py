"""Strategy selection: builds the decision-making policy actually used by
either turn loop in the repo, based on `config.yaml: strategy.algorithm`.
Keeps the algorithm choice in one place instead of scattering
if/else-on-algorithm checks through the engine and orchestrator.
"""

from src.strategy.heuristic import heuristic_candidate_actions, heuristic_policy
from src.strategy.q_learning import QLearningAgent, action_to_move


def build_local_policy(algorithm: str, q_agent: QLearningAgent | None = None):
    """Returns a Policy callable(board, agent) -> action, for
    src/engine/subgame.py / src/engine/game.py."""
    if algorithm == "q_learning":
        if q_agent is None:
            raise ValueError("q_learning policy requires a trained QLearningAgent")

        def policy(board, agent):
            barriers_remaining = board.max_barriers - board.barriers_placed
            action = q_agent.choose_action(board, barriers_remaining)
            if action is None:
                return heuristic_policy(board, agent)  # no legal action seen by the Q-table; fall back
            return action_to_move(action)

        return policy
    return heuristic_policy


def build_mcp_candidate_actions(algorithm: str, q_agents: dict[str, QLearningAgent] | None = None,
                                 visibility_radius: int | None = None):
    """Returns candidate_actions(agent, board, barriers_remaining, rng) ->
    list[action], for src/agents/orchestrator.py's try-until-accepted loop.
    The Q-table's pick goes first; the heuristic's full ranking follows as
    a fallback list, so the orchestrator never starves even on an
    unseen state or a rejected top pick.

    `visibility_radius` is baked into the closure (not threaded through the
    `policy_fn(agent, board, barriers_remaining, rng)` call signature
    itself, which every caller already relies on staying belief-agnostic
    per docs/PROMPTS.md) and passed straight through to
    `QLearningAgent.choose_action`. It only actually matters when `board`
    is a true (non-belief) board; against a belief-board proxy the
    explicit `UNKNOWN_POSITION` sentinel already on `board` takes priority
    regardless of this value (see `QLearningAgent.state_for`).
    """
    if algorithm == "q_learning" and q_agents:

        def candidate_actions(agent, board, barriers_remaining, rng):
            picked = q_agents[agent].choose_action(board, barriers_remaining, visibility_radius=visibility_radius)
            fallback = heuristic_candidate_actions(agent, board, barriers_remaining, rng)
            if picked is None:
                return fallback
            picked_action = action_to_move(picked)
            return [picked_action] + [a for a in fallback if a != picked_action]

        return candidate_actions
    return heuristic_candidate_actions
