"""Trains Cop and Thief Q-learning agents via repeated local sub-games (no
MCP, no LLM — offline tabular RL against the engine only; see
src/strategy/q_learning.py for why). Saves the trained Q-tables and a
learning-curve record under `results/q_tables/`, used for Phase 4's
GUI/report and the Phase 8 learning-curve figure.

Usage:
    python -m scripts.train_q_learning [--episodes N] [--grid ROWSxCOLS]
"""

import argparse
import json
from pathlib import Path

from src.config.loader import load_config
from src.engine.board import Board
from src.engine.start_positions import random_start_positions
from src.strategy.q_learning import QLearningAgent, legal_actions, step_reward

_RESULTS_DIR = Path(__file__).resolve().parents[1] / "results" / "q_tables"


def _run_training_subgame(board: Board, max_moves: int, cop_agent: QLearningAgent,
                           thief_agent: QLearningAgent) -> str:
    """One sub-game with a Q-update after every move; returns the winner."""
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

            state = agent.state_for(board)
            action = agent.choose_action(board, barriers_remaining)
            if action == "PLACE_BARRIER":
                board.place_barrier()
            else:
                board.move(agent_name, action)
            own_after = board.cop_pos if agent_name == "cop" else board.thief_pos

            captured = board.is_captured()
            reward = step_reward(agent_name, own_before, own_after, opponent_pos, captured)
            next_barriers_remaining = board.max_barriers - board.barriers_placed
            next_state = agent.state_for(board)
            next_actions = legal_actions(board, agent_name, next_barriers_remaining)
            agent.update(state, action, reward, next_state, next_actions)

            if captured:
                return "cop"
    return "thief"


def train(grid_size: tuple[int, int], max_moves: int, max_barriers: int, episodes: int,
          q_config: dict, seed: int = 0) -> tuple[QLearningAgent, QLearningAgent, list[dict]]:
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
        winner = _run_training_subgame(board, max_moves, cop_agent, thief_agent)

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=3000)
    parser.add_argument("--grid", type=str, default=None, help="ROWSxCOLS, defaults to config.board.grid_size")
    args = parser.parse_args()

    config = load_config()
    grid_size = tuple(config["board"]["grid_size"])
    if args.grid:
        rows, cols = args.grid.split("x")
        grid_size = (int(rows), int(cols))

    cop_agent, thief_agent, learning_curve = train(
        grid_size=grid_size,
        max_moves=config["game"]["max_moves"],
        max_barriers=config["game"]["max_barriers"],
        episodes=args.episodes,
        q_config=config["strategy"]["q_learning"],
    )

    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    cop_agent.save(_RESULTS_DIR / "cop_qtable.json")
    thief_agent.save(_RESULTS_DIR / "thief_qtable.json")
    with open(_RESULTS_DIR / "learning_curve.json", "w", encoding="utf-8") as f:
        json.dump({"grid_size": list(grid_size), "episodes": args.episodes, "curve": learning_curve}, f, indent=2)

    print(f"Trained {args.episodes} episodes on grid {grid_size}.")
    print(f"Final epsilon: cop={cop_agent.epsilon:.4f}, thief={thief_agent.epsilon:.4f}")
    print(f"Final cop_win_rate (last window): {learning_curve[-1]['cop_win_rate']:.3f}")
    print(f"Q-tables + learning curve saved to {_RESULTS_DIR}")


if __name__ == "__main__":
    main()
