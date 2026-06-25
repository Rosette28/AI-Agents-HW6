"""Offline Q-learning training loop, against the local engine directly (no
MCP, no LLM — thousands of training episodes over real network/tool calls
would be far slower for no benefit, since training has nothing to do with
the inter-agent NL channel; see `src.strategy.q_learning` for the full
state/action/reward design). Split out of `scripts/train_q_learning.py` to
keep that file as a thin CLI entrypoint under the project's 150-line limit.

Trains under the same partial-observability mechanic as the real game
(`config.yaml: observation.visibility_radius`) by default — each agent's
training state collapses the opponent's position to the shared "unknown"
bucket whenever they're out of range (`QLearningAgent.state_for`), instead
of always seeing the exact true position. Pass `visibility_radius=None` to
reproduce the original (pre-Phase-6) full-visibility training mode, kept
available for comparison, not because it's what the real game uses.
"""

from src.engine.board import Board
from src.engine.start_positions import random_start_positions
from src.strategy.q_learning import QLearningAgent, legal_actions, step_reward


def run_training_subgame(board: Board, max_moves: int, cop_agent: QLearningAgent,
                          thief_agent: QLearningAgent, visibility_radius: int | None) -> str:
    """One sub-game with a Q-update after every move; returns the winner.

    `visibility_radius=None` reproduces the original full-visibility
    training mode; an int simulates the real game's partial-observability
    mechanic against the true board (no NL channel here — see module
    docstring for why that's out of scope for offline training).
    """
    agents = {"cop": cop_agent, "thief": thief_agent}
    for _ in range(max_moves):
        for agent_name in ("thief", "cop"):
            agent = agents[agent_name]
            own_before = board.cop_pos if agent_name == "cop" else board.thief_pos
            opponent_pos = board.thief_pos if agent_name == "cop" else board.cop_pos
            barriers_remaining = board.max_barriers - board.barriers_placed

            actions = legal_actions(board, agent_name, barriers_remaining)
            if not actions:
                continue  # matches the engine's skip-on-no-legal-moves handling

            state = agent.state_for(board, visibility_radius=visibility_radius)
            action = agent.choose_action(board, barriers_remaining, visibility_radius=visibility_radius)
            if action == "PLACE_BARRIER":
                board.place_barrier()
            else:
                board.move(agent_name, action)
            own_after = board.cop_pos if agent_name == "cop" else board.thief_pos

            captured = board.is_captured()
            # Reward shaping uses the true positions (ground truth available
            # offline) even when the state key filed under is the "unknown"
            # bucket — the agent should still learn that closing/opening
            # real distance is good/bad, it just can't condition the
            # *state* on information it wouldn't have in the real game.
            reward = step_reward(agent_name, own_before, own_after, opponent_pos, captured)
            next_barriers_remaining = board.max_barriers - board.barriers_placed
            next_state = agent.state_for(board, visibility_radius=visibility_radius)
            next_actions = legal_actions(board, agent_name, next_barriers_remaining)
            agent.update(state, action, reward, next_state, next_actions)

            if captured:
                return "cop"
    return "thief"


def train(grid_size: tuple[int, int], max_moves: int, max_barriers: int, episodes: int,
          q_config: dict, visibility_radius: int | None = None,
          seed: int = 0) -> tuple[QLearningAgent, QLearningAgent, list[dict]]:
    cop_agent = QLearningAgent("cop", q_config["alpha"], q_config["gamma"],
                                q_config["epsilon"], q_config["epsilon_decay"])
    thief_agent = QLearningAgent("thief", q_config["alpha"], q_config["gamma"],
                                  q_config["epsilon"], q_config["epsilon_decay"])

    learning_curve = []
    window: list[int] = []
    for episode in range(1, episodes + 1):
        board = Board(grid_size, max_barriers)
        cop_pos, thief_pos = random_start_positions(grid_size)
        board.set_start_positions(cop_pos, thief_pos)
        winner = run_training_subgame(board, max_moves, cop_agent, thief_agent, visibility_radius)

        window.append(1 if winner == "cop" else 0)
        if len(window) > 100:
            window.pop(0)
        if episode % 50 == 0 or episode == episodes:
            learning_curve.append({
                "episode": episode,
                "cop_win_rate": sum(window) / len(window),
                "cop_epsilon": cop_agent.epsilon,
                "thief_epsilon": thief_agent.epsilon,
            })

        cop_agent.decay_epsilon()
        thief_agent.decay_epsilon()

    return cop_agent, thief_agent, learning_curve
