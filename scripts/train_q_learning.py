"""CLI entrypoint for training Cop and Thief Q-learning agents. Saves the
trained Q-tables and a learning-curve record under `results/q_tables/`,
used for Phase 4's GUI/report and the Phase 8 learning-curve figure. The
actual training loop lives in `src.strategy.q_learning_training` (kept
under the project's 150-line file limit by splitting the loop out of this
CLI wrapper); see that module's docstring for the partial-observability
training design.

Usage:
    python -m scripts.train_q_learning [--episodes N] [--grid ROWSxCOLS]
                                        [--full-visibility]
"""

import argparse
import json
from pathlib import Path

from src.config.loader import load_config
from src.strategy.q_learning_training import train

_RESULTS_DIR = Path(__file__).resolve().parents[1] / "results" / "q_tables"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=3000)
    parser.add_argument("--grid", type=str, default=None, help="ROWSxCOLS, defaults to config.board.grid_size")
    parser.add_argument("--full-visibility", action="store_true",
                         help="Train without the visibility-radius mechanic (legacy pre-Phase-6 mode)")
    args = parser.parse_args()

    config = load_config()
    grid_size = tuple(config["board"]["grid_size"])
    if args.grid:
        rows, cols = args.grid.split("x")
        grid_size = (int(rows), int(cols))

    visibility_radius = None if args.full_visibility else config["observation"]["visibility_radius"]

    cop_agent, thief_agent, learning_curve = train(
        grid_size=grid_size,
        max_moves=config["game"]["max_moves"],
        max_barriers=config["game"]["max_barriers"],
        episodes=args.episodes,
        q_config=config["strategy"]["q_learning"],
        visibility_radius=visibility_radius,
    )

    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    cop_agent.save(_RESULTS_DIR / "cop_qtable.json")
    thief_agent.save(_RESULTS_DIR / "thief_qtable.json")
    with open(_RESULTS_DIR / "learning_curve.json", "w", encoding="utf-8") as f:
        json.dump({
            "grid_size": list(grid_size),
            "episodes": args.episodes,
            "visibility_radius": visibility_radius,
            "curve": learning_curve,
        }, f, indent=2)

    print(f"Trained {args.episodes} episodes on grid {grid_size} "
          f"(visibility_radius={visibility_radius}).")
    print(f"Final epsilon: cop={cop_agent.epsilon:.4f}, thief={thief_agent.epsilon:.4f}")
    print(f"Final cop_win_rate (last window): {learning_curve[-1]['cop_win_rate']:.3f}")
    print(f"Q-tables + learning curve saved to {_RESULTS_DIR}")


if __name__ == "__main__":
    main()
