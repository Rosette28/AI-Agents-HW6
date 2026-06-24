"""Renders the Phase 3 Q-learning curve (results/q_tables/learning_curve.json,
produced by scripts/train_q_learning.py) to a PNG under figures/ — evidence
for the README/technical report per docs/TODO.md Phase 4's "produce
learning-curve graphs" item.

Run: python scripts/plot_learning_curve.py
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_CURVE_PATH = Path(__file__).resolve().parents[1] / "results" / "q_tables" / "learning_curve.json"
_OUT_PATH = Path(__file__).resolve().parents[1] / "figures" / "learning_curve.png"


def main() -> None:
    with open(_CURVE_PATH, encoding="utf-8") as f:
        data = json.load(f)

    episodes = [point["episode"] for point in data["curve"]]
    cop_win_rate = [point["cop_win_rate"] for point in data["curve"]]
    epsilon = [point["cop_epsilon"] for point in data["curve"]]

    rows, cols = data["grid_size"]
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(episodes, cop_win_rate, color="tab:red", label="Cop win rate")
    ax1.set_xlabel("Training episode")
    ax1.set_ylabel("Cop win rate", color="tab:red")
    ax1.set_ylim(0, 1.05)
    ax1.tick_params(axis="y", labelcolor="tab:red")

    ax2 = ax1.twinx()
    ax2.plot(episodes, epsilon, color="tab:blue", linestyle="--", label="Epsilon (exploration rate)")
    ax2.set_ylabel("Epsilon", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    plt.title(f"Q-learning convergence on a {rows}x{cols} grid ({data['episodes']} episodes)")
    fig.tight_layout()

    _OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(_OUT_PATH, dpi=150)
    print(f"Saved {_OUT_PATH}")


if __name__ == "__main__":
    main()
