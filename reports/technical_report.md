# Technical Report — Cop & Thief: MCP-Based Multi-Agent Pursuit Game

Phase 6 deliverable. This report covers everything answerable from the
implemented system and the real local run already completed; the sections
that genuinely depend on Phase 5's cloud deployment (public HTTPS logs,
final deployed-URL evidence) are marked explicitly rather than guessed at,
since that work is in progress in parallel and not yet confirmed from this
session.

## 1. Architecture overview

Full diagrams and ADRs live in `docs/PLAN.md`; summary:

- **Game Engine** (`src/engine/`) — the only ground-truth state owner. A
  configurable `Board` (any grid size), strict Thief-then-Cop turn
  alternation, capture/survival win conditions, barrier placement capped at
  `max_barriers`.
- **MCP Servers** (`src/mcp_servers/`) — two independently-deployable
  FastMCP services (Cop, Thief), each with its own `AgentSession` (own
  position, own barrier set, own inbox — ADR-5 in `docs/PLAN.md`). Neither
  server can see the other's true state; the orchestrator is the only thing
  that can, via its own `Board` mirror.
- **Agent Orchestrators** (`src/agents/`) — the MCP *Clients*. Each owns an
  LLM connection, a belief-update step, a strategy module, and the tool-call
  loop. This is where all LLM calls live; `src/mcp_servers/` imports no LLM
  SDK (verified by inspection, Phase 2).
- **Strategy** (`src/strategy/`) — Manhattan-distance heuristic (default)
  and Tabular Q-Learning, swappable via `config.yaml: strategy.algorithm`,
  both belief-agnostic (consume a `Board` with the opponent's position
  already replaced by the current belief estimate).
- **Reporting** (`src/reporting/`) — assembles and validates the Internal
  Game JSON, sends it via the Gmail API as the sole content of the report
  email.
- **GUI** (`src/gui/`) — Streamlit app polling a JSON state-snapshot file
  written by the orchestrator after every turn.

## 2. Dec-POMDP formal model

The generic tuple is `⟨n, S, {Ai}, P, R, {Ωi}, O, γ⟩` (see
`docs/CONCEPTS.md` for the generic definitions). Mapped concretely onto
this codebase:

| Symbol | Generic meaning | This project's instantiation |
|---|---|---|
| `n` | number of agents | 2 — Cop and Thief, each one `AgentOrchestrator` + one independent MCP server |
| `S` | full state space | `(cop_pos, thief_pos, barrier_set, move_count)` — the orchestrator's private `Board` mirror (`src/engine/board.py`) is the only place this full tuple ever exists at once |
| `A_cop` | Cop's action set | 8 movement directions + `place_barrier` (capped at `max_barriers`, rejected once exhausted by `Board.place_barrier`) |
| `A_thief` | Thief's action set | 8 movement directions only — `choose_action(place_barrier=True)` is rejected server-side for the Thief (`src/mcp_servers/factory.py`) |
| `P` | transition function | Deterministic given a legal action; illegal moves (off-board, into a barrier) are rejected as no-ops, not silently corrected — `Board.move()` |
| `R` | reward function | The scoring table in `config.yaml` (`scoring.cop_capture`, `scoring.thief_survival`, etc.), realized terminally per sub-game by `src/engine/results.py`; Q-learning additionally uses a per-step Δ-Manhattan-distance shaping reward, *internal* to training and never part of the graded score |
| `Ω_cop`, `Ω_thief` | per-agent observation space | own exact position (always); opponent's exact position *only* if within `config.yaml: observation.visibility_radius` (`observe_opponent` MCP tool); otherwise nothing but whatever the opponent's NL message claims |
| `O` | observation function | `observe_opponent(opponent_position)` for the in-radius case (ground truth, supplied by the orchestrator, since no server holds the opponent's position itself per ADR-5); for the out-of-radius case, `src/agents/belief.py:update_belief()` — an LLM call that extracts a positional/intent estimate from free text, which may be truthful, vague, or actively misleading |
| `γ` | discount factor | `config.yaml: strategy.q_learning.gamma` (0.9 in the calibrated run) — used only by the Q-learning strategy layer, not by the heuristic |

**Where this departs from the textbook tuple, and why it matters:** in a
standard Dec-POMDP, `O` is a single fixed stochastic function of the true
state. Here, `O` has two channels with very different reliability: the
visibility-radius observation is *exact but rare*, while the NL channel is
*always available but adversarially noisy* (the Thief's strategy
deliberately injects misleading observations into it via
`choose_deception_level`). `src/agents/belief.py` resolves this by treating
direct observation as an override that always wins when available, and the
NL-derived estimate as a fallback that decays in confidence the vaguer the
message is — see §3 for a concrete transcript example of this in action.

## 3. Orchestration-challenge analysis

This is the assignment's core engineering challenge: no fixed message
schema between agents, just free text parsed by an LLM at each turn. Three
concrete difficulties surfaced during the real 6-sub-game run
(`results/transcripts/subgame_5x5_0{1-6}_*.txt`, Anthropic
`claude-haiku-4-5-20251001`, recorded 2026-06-24):

**(a) Deliberate self-contradiction (bluffing) is indistinguishable, at the
text level, from a model being simply wrong.** Sub-game 1, Turn 33: the
Thief's message read *"I'm heading south toward the river district, nowhere
near the north end,"* while its logged action was `{'type': 'move',
'direction': 'N'}` — the exact opposite. This was `choose_deception_level`
correctly picking `"mislead"` for that turn, not a parsing failure. The
design choice (`docs/prd/nl-dialogue.md`'s edge-case rule) was to log the
mismatch and let the opponent's belief-update LLM call decide how much
weight to give it, rather than have the orchestrator "correct" or flag it
as an error — doing otherwise would silently leak ground truth across the
belief boundary the whole assignment is built to test.

**(b) Genuine vagueness has to be treated as a first-class outcome, not an
error path.** Across all 6 transcripts, nearly every message the
belief-update call classified as `"no reliable information"` was a
legitimately vague spatial description (e.g. *"I'm somewhere in the middle
of the grid, heading toward the edges"*) rather than an API/JSON failure.
`docs/prd/nl-dialogue.md` requires this explicitly — "no reliable
information" must be a valid extraction outcome, not something the system
treats as broken. The qualitative read confirms the belief module's
confidence labeling tracked actual message vagueness, not parsing
robustness.

**(c) Belief uncertainty has a visible, sometimes degenerate, effect on
physical behavior.** In sub-games where the Thief's belief stayed at "no
information" for long stretches, its actual movement oscillated almost
entirely between two cells, `(0,0)` and `(1,0)`. Root cause:
`make_belief_board` defaults an unknown opponent position to the grid
center (`(2,2)` on 5×5), and the Thief's heuristic ("maximize distance from
believed opponent position") then deterministically points toward the same
two corner cells whenever there's no real signal to act on. This is not a
bug in the engine or the MCP wiring — it is what a distance-maximizing
heuristic *should* do given a fixed default belief — but it's a clean
illustration of how a belief-update design choice (what to default an
unknown position *to*) directly shapes physical-layer behavior, which is
exactly the kind of orchestration subtlety a rigid coordinate protocol
would never surface, because there would be no "unknown" to default in the
first place.

**Mitigation adopted, not a fix:** none of the three behaviors above were
"fixed," because they are the correct behavior of the design as specified
(bluffing is supposed to happen; vagueness is supposed to degrade
gracefully; a fixed default belief is supposed to produce some
deterministic fallback action). The mitigation was making each one
*visible* — transcript logging, belief-confidence labeling, and this
write-up — rather than papering over them with hidden correction logic
that would defeat the point of testing free-NL orchestration in the first
place.

## 4. Results across the sanity-check grid-size progression

All recorded in `docs/TODO.md`'s notes log; summarized here.

**Stage 1 — random placeholder policy (`policy_stub`), MCP chain, no LLM,
seed=99, 6 sub-games per grid:**

| Grid | Cop wins | Thief wins | Moves-to-capture range | Notes |
|---|---|---|---|---|
| 1×2 | 6/6 | 0 | 1 | smallest possible board — Thief has nowhere to go |
| 2×3 / 3×2 | 6/6 | 0 | 1–6 | |
| 3×4 / 4×3 | 6/6 | 0 | 2–19 | more room → longer random walks before collision |
| 5×5 | 5/6 | 1 | up to the 25-move cap | the one Thief win is the move-cap survival, not evasion |

Interpretation: a uniformly random Thief isn't evading anything — it
"wins" only when its random walk happens to dodge the Cop for 25 moves,
which is mechanically more likely on a larger board. This validated the
MCP wiring and Phase 1 capture semantics carrying through unchanged; it is
not a balance signal about the engine itself.

**Stage 2 — heuristic / Q-learning strategy (Phase 3), local engine,
5×5, no partial observability yet:** Cop win-rate rose from 0.74 (episode
50 of Q-learning training) to 1.0 by ~episode 1300, held through 4000
episodes — see §5. Full Manhattan-distance dominance once both sides have
*some* directed strategy and *full* visibility is consistent with the
random-policy stage also favoring the Cop on 5×5: with no information
asymmetry, a pure distance-closer beats a pure distance-maximizer, since
the Cop's win condition (`exact cell match`) is strictly easier to satisfy
than the Thief's (`survive every single move`).

**Stage 3 — real LLM-driven run with partial observability + NL bluffing
(Phase 4), 5×5, `claude-haiku-4-5-20251001`, 6 sub-games:**

> **Final totals: Cop 75, Thief 45.** Cop won sub-games 2, 3, 4 by capture
> (in 2, 12, and 11 moves respectively); Thief won sub-games 1, 5, 6 by
> surviving the full 25-move cap.

This is the result that matters most for the central claim: once the Cop
loses unconditional visibility and the Thief gains a real NL deception
lever, the Thief wins 3 of 6 sub-games — a complete reversal from both
earlier stages, where the Cop swept or nearly swept. Partial observability
and bluffing are doing real work, not just existing on paper.

## 5. Learning curve

`results/q_tables/learning_curve.json` (raw data) →
`figures/learning_curve.png` (rendered by `scripts/plot_learning_curve.py`).
Rolling (window=100) Cop win-rate climbs from 0.74 at episode 50 to a
stable 1.0 by episode ~1300, holding there through the full 4000-episode
run — clean, monotonic convergence with no oscillation, using the
`config.yaml` defaults (α=0.1, γ=0.9, ε₀=0.2, decay=0.995, floor=0.01).
Full reasoning for keeping these defaults (rather than retuning) is in
`docs/prd/strategy.md`'s calibration record — the first run converged
cleanly enough that there was nothing to fix.

## 6. GUI

`src/gui/app.py` (Streamlit) polls `src/gui/state_writer.py`'s JSON
snapshot, showing the live grid, both agents' positions, barriers, and each
agent's belief note/confidence alongside the true state. Covered by code
review and `tests/gui/test_state_writer.py`.

**Pending:** an actual browser screenshot of the running GUI for this
report — needs a live run (`streamlit run src/gui/app.py` alongside
`scripts/run_llm_demo.py`) captured by you; this session has no display.
Slot it in under this section once captured.

## 7. Cloud deployment status (Phase 5, in progress in parallel)

`config/config.yaml: mcp.{cop,thief}_mcp_url` already point at Render
deployments. Per the project's own Phase 5 checklist, what's still
*unconfirmed from this session* is: public-HTTPS reachability from outside
your network (`scripts/check_cloud_reachability.py` is the tool for this —
run it once both servers and `.env`'s `COP_MCP_AUTH_TOKEN`/
`THIEF_MCP_AUTH_TOKEN` are set), and a real Gmail OAuth send (credential
paths + `config.yaml: group.*`, currently empty placeholders). Once both
are confirmed, this section should be replaced with: the two final URLs,
a `check_cloud_reachability.py` transcript proving reachability from
outside your network, and confirmation of one real email received. None of
the Phase 6 analysis above depends on this being finished first.

## 8. The four required questions

**How does free-language orchestration differ from a rigid protocol?**
A rigid protocol (e.g. JSON with a `position` field) would make belief
update a lookup, not an inference — there would be nothing to parse,
nothing to default when information is missing, and no room for bluffing.
Free NL forces every turn's belief update through an LLM call that has to
handle three outcomes — direct extraction, "no reliable information," and
detected self-contradiction — none of which exist in a rigid schema. §3
above walks through concrete transcript evidence of all three.

**How did partial observability shape the belief-update logic?**
It created the override hierarchy in `src/agents/belief.py`: direct
observation (when in `visibility_radius`) always wins over the NL-derived
estimate, never the reverse, because the NL channel is adversarially
unreliable while the visibility-radius channel is exact-but-rare. It also
forced a decision about what to believe when there is genuinely *no*
signal at all (neither in-radius nor a usable NL hint) — the chosen default
(grid center) turned out to have a visible behavioral side effect (§3(c)),
which would never have surfaced under full observability.

**Where did the strategy's "skill ceiling" show up?**
Two places. First, mechanically: Q-learning converges cleanly to a 1.0 Cop
win-rate under full observability (§5) — there, the "skill ceiling" is just
a stronger version of the heuristic's own logic, because full information
makes the problem easy for any directed strategy. Second, and more
interestingly: once partial observability and NL bluffing were layered on
in Phase 4, the *heuristic* strategy (not Q-learning, which trained only
under full observability and was not retrained against a belief-noisy
opponent) produced the Thief's 3-of-6 win reversal in the real LLM run —
the skill ceiling that actually mattered for the assignment's central claim
came from the orchestration layer (belief + deception), not from the
decision-making algorithm underneath it. This is worth flagging plainly:
the Q-learning tables in `results/q_tables/` were trained under full
visibility and were not the strategy in use during the real Phase 4 run —
the heuristic was. Retraining Q-learning against a belief-board input
(rather than the true board) is a natural next step, not yet done.

**What were the cloud deployment's security trade-offs?**
Token-based bearer auth per server, with revocation enforced by re-reading
an on-disk revocation list on every request rather than only at server
startup (`src/mcp_servers/auth.py:RevocableTokenVerifier`) — the trade-off
chosen there was a small per-request disk read in exchange for not needing
a server restart to make a revocation take effect immediately, which
matters if a token needs to be cut off mid-series. The broader cloud
security picture (firewall posture, TLS termination specifics on the
hosting platform, exact reachability evidence) is still pending
confirmation per §7 above and should be filled in here once available —
this report does not overstate that as done.

## 9. Status note

Sections 1–6 and 8 (except the security-trade-offs half answered with full
evidence) are complete and based on real, already-recorded runs — not
projected or assumed. Section 7 and the GUI screenshot slot in §6 are the
two places this report explicitly defers to work in progress outside this
session, per the project's own Phase 5/6 dependency split documented in
`docs/TODO.md`.
