# Mini-PRD — Strategy / Decision-Making

## Description / theoretical background

The strategy module decides what action an agent's orchestrator should take
once it has an updated belief about the board state. Two tiers, both
allowed by the assignment: a heuristic baseline (Manhattan distance /
simple decision rules) and an optional Tabular Q-Learning layer as the
"skill ceiling." This module is decoupled from the NL-parsing/belief-update
logic — it only consumes a belief state and returns an action.

## Requirements, inputs/outputs

- **Input:** current belief state — own exact position, believed opponent
  position (point estimate or distribution within `visibility_radius`),
  barrier layout, moves remaining, barriers remaining (Cop).
- **Output:** one action — a direction to move, or (Cop only) place_barrier.

## Algorithm

**Heuristic (baseline):**
- Cop: move along the direction that minimizes Manhattan distance to the
  believed Thief position; if adjacent to the believed position and no
  capture is possible this turn, consider a barrier to cut off an escape
  route.
- Thief: move along the direction that maximizes Manhattan distance from
  the believed Cop position, subject to board/barrier constraints.

**Tabular Q-Learning (optional, layered on top):**
- State `s`: discretized own position + believed opponent position (and
  optionally barrier layout) within the current grid size.
- Action `a`: one of the 8 directions (+ barrier for Cop).
- Reward `r`: shaped per-step reward (e.g. Δdistance) plus terminal
  sub-game reward from the scoring table.
- Policy: epsilon-greedy, `epsilon` decaying per `config.yaml`.
- Update: `Q(s,a) ← Q(s,a) + α[r + γ·max_a′ Q(s′,a′) − Q(s,a)]`.
- Q-table persisted to `results/` after training so learning curves can be
  reconstructed.

## Constraints and limitations, alternatives considered

- Q-learning's state space grows with grid size — must remain tractable up
  to 5×5; if it doesn't converge in a reasonable number of episodes, fall
  back to documenting that limitation rather than forcing deep RL (out of
  scope per requirements §10).
- **Alternative considered:** decision trees — viable but Manhattan-distance
  heuristic is simpler to reason about and sufficient to de-risk the
  orchestration work first.

## Success criteria / test scenarios

- Unit tests for the Bellman update (correct Q-value given a known
  transition) and for epsilon-greedy action selection (statistically,
  over many trials, respects the configured epsilon).
- Calibration record (chosen α, γ, ε, ε-decay, and why) kept in this file
  once tuned.
- Documented uniqueness note: how this implementation differs from any code
  shared with a partner group, per the assignment's originality requirement.
