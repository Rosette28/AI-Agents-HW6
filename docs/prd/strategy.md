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
  opponent_pos)` string key, where `opponent_pos` collapses to one shared
  `"?"` bucket whenever the opponent is out of `visibility_radius` —
  during training, checked against the true board (no NL channel
  simulated); at inference, against the `UNKNOWN_POSITION` sentinel
  already on the belief-board proxy (`src.agents.belief.make_belief_board`)
  whenever there's no usable estimate. Action = one of the 8 directions,
  plus `PLACE_BARRIER` for the Cop. Reward = per-step Δ-Manhattan-distance
  toward the agent's goal (computed from the *true* positions, even when
  filed under the "unknown" state bucket), ±50 terminal bonus on capture.
  Q-tables persist to `results/q_tables/{cop,thief}_qtable.json`;
  `src/strategy/policy.py` selects between heuristic and Q-learning per
  `config.yaml: strategy.algorithm`, exposing both the `Policy` and
  candidate-list interfaces so either turn loop can use either algorithm
  without code changes elsewhere.
- **Calibration record, partial-observability retrain (2026-06-25, the
  current default — supersedes the full-visibility-only run below)**:
  4000 episodes, 5×5 grid, `config.yaml` defaults (α=0.1, γ=0.9, ε₀=0.2,
  ε-decay=0.995, floor=0.01, `observation.visibility_radius=2`). Rolling
  (window=100) Cop win-rate does **not** converge cleanly the way the
  full-visibility run did — it oscillates noisily between roughly 0.23
  and 0.69 across the full run, ending at 0.38 (episode 4000), with no
  stable plateau at any point after epsilon reaches its floor (~episode
  600). This is a real, reproducible finding, not a bug: once both
  agents' opponent-position observation collapses to a single shared
  `"?"` state whenever out of radius, that bucket aggregates many
  genuinely different true game situations under one Q-value per action —
  a fundamentally non-stationary target for a tabular learner, since the
  "right" action when truly blind legitimately varies turn to turn. The
  table still learns useful values for the *in-radius* states (those
  behave like the old full-visibility case), it just can't converge on a
  single best policy for the "unknown" bucket the way it could when there
  was no such bucket at all. Raw curve:
  `results/q_tables/learning_curve.json`; figure: `figures/learning_curve.png`.
  No retuning attempted — the oscillation is a property of the state
  representation under partial observability, not the hyperparameters; a
  higher α/lower γ wouldn't fix a fundamentally non-stationary bucket.
- **Calibration record, original full-visibility-only run (2026-06-23,
  superseded above, kept here for comparison)**: same 4000 episodes/5×5
  grid/hyperparameters, but with no visibility-radius mechanic at all
  (every state saw the exact true opponent position). ε decayed to its
  0.01 floor by ~episode 900; Cop win-rate rose from 0.74 at episode 50 to
  a clean, monotonic 1.0 by episode ~1300, held through episode 4000, no
  oscillation. Reproduced exactly via `scripts/train_q_learning.py
  --full-visibility`; archived at
  `results/q_tables/learning_curve_full_visibility_baseline.json`.
- **What this means for the report's skill-ceiling discussion:** the
  original full-visibility result was solving an easier problem than the
  one actually graded (see `reports/technical_report.md` §8, which flagged
  exactly this gap). The partial-observability retrain is what's now
  actually relevant to the real game — and the headline finding is that
  full Cop dominance was *entirely an artifact of full visibility*: once
  the same Manhattan-distance-driven reward signal has to operate through
  the same "unknown" bucket the real game's belief system produces, the
  Cop's structural advantage (capture is an easier target than survival)
  is no longer enough to guarantee a clean win — consistent with the real
  LLM-driven run's own reversal (Thief winning 3 of 6 sub-games, §4 of the
  technical report), just reached here via a completely different
  mechanism (training-time state-space limitation vs. a real LLM's NL
  bluffing).
- **Cop dominance under full visibility is consistent with the Phase 2
  random-policy sanity progression** (also Cop-favored on 5×5, 5/6 wins):
  with no information asymmetry, the Cop's pure distance-closing pressure
  out-paces a Thief whose only lever is also distance, since capture
  (exact match) is an easier target than survival (never match, ever).
  That asymmetry is exactly what partial observability erodes, per above.
- **Originality / uniqueness note** — this Manhattan-distance heuristic and
  this specific Q-learning state/action/reward design are this project's
  own, written without reference to any other group's implementation. The
  inter-group bonus (Phase 7) is currently deferred, so no code is shared
  with a partner group; if that changes, this section will be updated with
  the concrete diff between what's shared and what stays unique to this
  project's agents.
