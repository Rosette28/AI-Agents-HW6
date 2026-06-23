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

## Implementation notes (Phase 3, done)

- **Heuristic** — `src/strategy/heuristic.py`. Two entry points over the
  same Manhattan-distance ranking: `heuristic_policy(board, agent)` for the
  local engine's `Policy` interface (`src/engine/subgame.py`,
  `src/engine/game.py`), and `heuristic_candidate_actions(agent, board,
  barriers_remaining, rng)` for the MCP orchestrator's try-until-accepted
  loop (`src/agents/orchestrator.py`) — now the orchestrator's default
  `policy_fn`, replacing the Phase 2 random `policy_stub`. Cop barricades
  when adjacent to the Thief (distance 1) and barriers remain, since
  `Board.place_barrier()` walls off the Cop's *current* cell, denying it as
  an escape route once the Cop steps off next turn — not a target cell, so
  it's only useful right at the moment of closing in.
- **Tabular Q-Learning** — `src/strategy/q_learning.py` (`QLearningAgent`)
  + `scripts/train_q_learning.py` (offline training loop against the local
  engine directly, not through MCP — thousands of training episodes over
  real tool calls would be far slower for no benefit, since training has
  nothing to do with the inter-agent NL channel). State = `(own_pos,
  opponent_pos)` string key; action = one of the 8 directions, plus
  `PLACE_BARRIER` for the Cop. Reward = per-step Δ-Manhattan-distance
  toward the agent's goal, ±50 terminal bonus on capture. Q-tables persist
  to `results/q_tables/{cop,thief}_qtable.json`; `src/strategy/policy.py`
  selects between heuristic and Q-learning per `config.yaml:
  strategy.algorithm`, exposing both the `Policy` and candidate-list
  interfaces so either turn loop can use either algorithm without code
  changes elsewhere.
- **Calibration record** (trained 2026-06-23, 4000 episodes, 5×5 grid,
  `config.yaml` defaults: α=0.1, γ=0.9, ε₀=0.2, ε-decay=0.995, floor=0.01):
  ε decayed to its 0.01 floor by ~episode 900; rolling (window=100)
  Cop win-rate rose from 0.74 at episode 50 to 1.0 by episode ~1300 and
  held there through episode 4000 — clean, monotonic convergence, no
  oscillation or instability at any point. α=0.1 (gentle, stable updates;
  the state space here is small enough — ≤625 `(own, opponent)` pairs per
  grid size — that a higher α wasn't needed to converge fast) and γ=0.9
  (heavily weight the terminal capture/evade outcome over short-term
  positional drift, since the per-step Δ-distance shaping is already doing
  the short-term work) were kept at the config defaults because the first
  run converged cleanly; no retuning was needed. Raw curve:
  `results/q_tables/learning_curve.json`.
- **Cop dominance is consistent with the Phase 2 random-policy sanity
  progression** (also Cop-favored on 5×5, 5/6 wins), not a Q-learning
  artifact: on an unbounded-visibility 5×5 grid the Cop's pure
  distance-closing pressure (now reinforced, not random) out-paces a
  Thief whose only lever is also distance — there's no information
  asymmetry yet to favor evasion. This is expected to shift materially in
  Phase 4 once partial observability (`observation.visibility_radius`) and
  NL-channel bluffing give the Thief real tools the Cop can't see through
  by definition. Worth re-measuring once Phase 4 lands, not before.
- **Originality / uniqueness note** — this Manhattan-distance heuristic and
  this specific Q-learning state/action/reward design are this project's
  own, written without reference to any other group's implementation. The
  inter-group bonus (Phase 7) is currently deferred, so no code is shared
  with a partner group; if that changes, this section will be updated with
  the concrete diff between what's shared and what stays unique to this
  project's agents.
