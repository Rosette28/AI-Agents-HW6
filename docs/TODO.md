# TODO — Task Tracker

This file is the live task breakdown for the project, organized by the same
phases as `hw06_project_plan.md`. No tables — each task is a checklist item
with its priority, owner, current status, and definition of done spelled
out underneath it, so it stays readable as it grows. Update statuses as you
go; don't let this drift from reality. Status values used below: **not
started**, **in progress**, **blocked**, **done**.

---

## Phase 0 — Orientation, Planning Docs, Environment & Repo Setup

- [ ] **Re-watch the L09 recording and read the course's "AI-agent software
  submission recommendations" file**
  - Priority: High
  - Owner: unassigned
  - Status: not started
  - Why it matters: grading is partly based on this recommendations file,
    and it directly shapes what goes into `docs/PROMPTS.md`.
  - Definition of done: notes captured somewhere durable (this file or
    `docs/PROMPTS.md`), and any guidance from it reflected in the agent
    rules already drafted.

- [x] **Write `docs/CONCEPTS.md`**
  - Priority: High
  - Owner: unassigned
  - Status: done
  - Definition of done: every core concept (MCP Client/Server split,
    Dec-POMDP tuple, partial observability, Q-learning building blocks,
    token auth + revocation, the three LLM-deployment approaches) is listed
    with an explanation of how *this* project instantiates it, not just the
    generic textbook definition.

- [x] **Create the GitHub repo, add `.gitignore` and `LICENSE`**
  - Priority: High
  - Owner: unassigned
  - Status: done locally — needs `git init` / first commit, which you run
    yourself
  - Definition of done: repo skeleton on disk matches the target layout in
    `docs/PLAN.md`; `.gitignore` excludes Python artifacts, `.env`, and
    `logs/`; `LICENSE` present at repo root.

- [x] **Write `docs/PRD.md` and get it approved**
  - Priority: High
  - Owner: unassigned
  - Status: done, pending your read-through and sign-off
  - Definition of done: states the central claim ("two independent AI
    agents communicating only in free natural language through separate
    MCP servers can autonomously play a complete 6-round pursuit game and
    self-report the result"), goals/KPIs, functional and non-functional
    requirements, assumptions/constraints/out-of-scope, and a timeline.

- [x] **Write `docs/PLAN.md`**
  - Priority: High
  - Owner: unassigned
  - Status: done
  - Definition of done: module breakdown and data flow (game engine → MCP
    servers → agent orchestrators → NL dialogue → scoring → email report)
    are documented, along with the chosen LLM-deployment approach and the
    reasoning behind it (ADRs).

- [ ] **Write a mini-PRD per mechanism under `docs/prd/`**
  - Priority: Medium
  - Owner: unassigned
  - Status: in progress — first drafts exist for all six (game-engine,
    mcp-servers, strategy, nl-dialogue, email-reporting, bonus-inter-group);
    treat them as living documents to revisit once each mechanism is
    actually implemented, since assumptions made on paper will shift.
  - Definition of done per mini-PRD: inputs/outputs, algorithm, edge cases,
    and success criteria sections are accurate to the *implemented* code,
    not just the planned design.

- [ ] **Write `docs/PROMPTS.md` and the agent guidelines**
  - Priority: High
  - Owner: unassigned
  - Status: in progress — first draft exists (modular-architecture rules +
    Cop/Thief system prompts + belief-update prompt pattern); needs a pass
    once the L09 recommendations file has been re-read, and needs real
    tuning once agents are actually talking to each other and producing
    transcripts worth reading.
  - Definition of done: the modular-architecture rules are followed in
    practice (spot-check against actual `src/` files), and the system
    prompts produce coherent, rule-abiding NL behavior in a real run, not
    just on paper.

- [ ] **Confirm the exact submission date/time with the instructor**
  - Priority: High
  - Owner: unassigned
  - Status: deferred — not relevant right now
  - Why it matters: the source material has a contradiction between
    "Friday 08:30" and a fixed calendar date; this needs resolving before
    Phase 8 planning gets serious.

- [ ] **Bonus: contact a partner group and agree on a work split**
  - Priority: Low
  - Owner: unassigned
  - Status: deferred — not pursuing the bonus right now
  - Definition of done (if revisited): partner group identified, and
    `docs/PLAN.md` updated with what's shared (code/architecture) vs. what
    stays unique to each group (agent implementation + internal strategy).

- [ ] **Watch the Gmail dashboard / token-creation recording**
  - Priority: Medium
  - Owner: unassigned
  - Status: not started
  - Definition of done: watched before any code in `src/reporting/` is
    written, since the Google Cloud project + OAuth setup it walks through
    is a prerequisite for that module.

- [ ] **Create an isolated environment (e.g. `uv venv`) and install deps**
  - Priority: High
  - Owner: unassigned
  - Status: not started
  - Definition of done: `uv venv && uv pip install -r requirements.txt`
    succeeds cleanly; exact installed versions get pinned back into
    `requirements.txt`/`pyproject.toml` once known-compatible.

- [ ] **Populate `.env` from `.env.example`**
  - Priority: High
  - Owner: unassigned
  - Status: not started
  - Definition of done: LLM API key and (later) Gmail OAuth credential
    paths are filled in locally; `.env` itself stays out of git (already
    covered by `.gitignore`).

- [x] **Create the `config/config.yaml` skeleton**
  - Priority: High
  - Owner: unassigned
  - Status: done
  - Definition of done: every parameter from the requirements table is
    present (`grid_size`, `max_moves`, `num_games`, `max_barriers`, all four
    `scoring.*` values), plus the extra knobs this project needs
    (`observation.visibility_radius`, `llm.*`, `strategy.q_learning.*`,
    `mcp.*`, `reporting.recipient_email`). Nothing downstream should ever
    hardcode a value that belongs here.

---

## Phase 1 — Game Engine & Rules (local, no agents yet)

Build and verify this deterministically before any MCP or LLM wiring —
that's the whole point of doing it as its own phase.

- [x] **Implement the board as a state machine with a configurable grid
  size**
  - Priority: High
  - Status: done — `src/engine/board.py`; `Board(grid_size, max_barriers)`
    takes grid size as a constructor arg, never hardcoded.
  - Definition of done: grid size is read from `config.board.grid_size`;
    nothing in the engine assumes 5×5; the same code path handles a 1×2
    board and a 5×5 board identically.

- [x] **8-directional movement with boundary validation**
  - Priority: High
  - Status: done — `Board.move()` + `DIRECTIONS` dict in
    `src/engine/board.py`; covered by `tests/engine/test_board.py`.
  - Definition of done: all 8 directions (N, S, E, W, NE, NW, SE, SW) are
    supported; moves off the board are rejected with a clear reason, not a
    crash.

- [x] **Turn order (Thief moves first, then Cop, repeating)**
  - Priority: High
  - Status: done — `run_subgame()` in `src/engine/subgame.py` alternates
    thief/cop strictly per move number.
  - Definition of done: the engine enforces strict alternation and exposes
    whose turn it is at any point in a sub-game.

- [x] **Barrier placement (Cop only, capped at `max_barriers`)**
  - Priority: High
  - Status: done — `Board.place_barrier()`; no-legal-moves fallback
    (skip turn) implemented in `run_subgame()` for the Thief; Cop retains
    the option to barricade even with no legal moves. Covered by the
    1×2 sanity tests.
  - Definition of done: only the Cop can place a barrier; barriers block
    both agents from entering that cell for the rest of the sub-game; the
    Cop cannot exceed `max_barriers` placements in one sub-game; placing a
    barrier on the Cop's own current cell does not trap the Cop with zero
    legal moves (decide and implement a no-legal-moves fallback, e.g. skip
    turn).

- [x] **Win conditions: capture and survival**
  - Priority: High
  - Status: done — `Board.is_captured()` checked after every move in
    `run_subgame()`; survival declared at `max_moves` with no capture.
  - Definition of done: capture is detected the instant the Cop's position
    exactly matches the Thief's; survival is declared once the Thief
    completes `max_moves` without ever being captured.

- [x] **Sub-game loop (≤25 moves) and full-game loop (6 sub-games)**
  - Priority: High
  - Status: done — `src/engine/subgame.py` (sub-game) and
    `src/engine/game.py` (`run_game_series`, accumulates cop/thief totals
    per the scoring table across `num_games` sub-games).
  - Definition of done: a sub-game terminates correctly on capture,
    survival, or the move cap; a full series runs exactly `num_games`
    sub-games back to back and accumulates per-sub-game scores into a
    series total matching the scoring table.

- [x] **Persist every raw sub-game result to `results/*.json`**
  - Priority: Medium
  - Status: done — `src/engine/results.py` (`save_subgame_result`),
    called from `run_game_series` after each sub-game.
  - Definition of done: each result file is tagged by scenario (grid size,
    sub-game index, winner) and is written automatically, never
    hand-edited afterward.

- [x] **Sanity check on a 1×2 grid**
  - Priority: High
  - Status: done — `tests/engine/test_sanity_1x2.py` covers capture,
    survival, self-barricade-with-no-legal-moves, and full 6-sub-game
    scoring on a 1×2 board.
  - Definition of done: win conditions, barrier logic, and scoring all
    behave correctly on the smallest possible board, run before scaling up
    to anything larger — this is meant to catch off-by-one and edge-case
    bugs cheaply.

- [x] **Unit tests: movement validation, barrier blocking, capture
  detection, survival detection, score accumulation**
  - Priority: High
  - Status: done — `tests/engine/` (`test_board.py`, `test_subgame.py`,
    `test_game.py`, `test_results.py`, `test_start_positions.py`,
    `test_sanity_1x2.py`) plus `tests/config/test_loader.py`. 21 tests
    passing, 98% coverage on `src/engine` + `src/config` (target ≥85%).
  - Definition of done: each of these five behaviors has a dedicated,
    passing test, and the suite catches a deliberately-introduced
    regression in any one of them.

---

## Phase 2 — MCP Infrastructure & Full Local Run

- [x] **Stand up two MCP servers (Cop, Thief) using FastMCP**
  - Priority: High
  - Status: done — `src/mcp_servers/cop_server.py` and `thief_server.py`,
    each a thin wrapper that builds a FastMCP instance from the shared
    `src/mcp_servers/factory.py` tool-registration logic (kept in one place
    to avoid duplicating the tool bodies between the two otherwise-identical
    servers). Each is independently startable on its own port via
    `scripts/run_mcp_servers.py`.
  - Definition of done: each server lives in its own module under
    `src/mcp_servers/`, runs on its own port, and is independently
    startable/stoppable. Verified manually with both servers bound to
    `127.0.0.1:8001`/`8002` simultaneously.

- [x] **Expose the required tools on each server**
  - Priority: High
  - Status: done — `ping`, `read_message`, `send_message`,
    `report_location`, `choose_action` all implemented in
    `src/mcp_servers/factory.py`; `report_location` only ever returns the
    calling agent's own position, and `choose_action(place_barrier)` is
    rejected for the Thief.
  - Definition of done: matches `docs/API.md`. Covered by
    `tests/mcp_servers/test_tools.py`.

- [x] **Document each tool's contract in `docs/API.md`**
  - Priority: High
  - Status: done — the existing draft contract matched the implementation
    exactly once built; no changes needed.
  - Definition of done: the doc accurately reflects the real request/
    response shape of every tool, including error formats.

- [x] **Confirm Client/Server separation**
  - Priority: High
  - Status: done — `src/mcp_servers/` has no import of `anthropic` or any
    LLM SDK; the one decision-making module that exists so far
    (`src/agents/policy_stub.py`) is a non-LLM placeholder (random legal
    action), living under `src/agents/` per the required split. Real LLM
    calls arrive in Phase 3/4 and will stay in `src/agents/`.
  - Definition of done: grep/inspect confirms no LLM import in
    `src/mcp_servers/`.

- [x] **Run both servers locally on separate ports, verify mutual
  reachability with a trivial ping/echo tool call**
  - Priority: High
  - Status: done — `scripts/run_mcp_servers.py` starts both servers (ports
    from `config.yaml: mcp.*`) in one process as concurrent asyncio tasks,
    sharing one `GameSession`; manually verified a `ping` round-trip against
    both `http://127.0.0.1:8001/mcp` and `:8002/mcp`, plus a `send_message`
    on the Thief's port correctly arriving in the Cop's `read_message`.
    Automated equivalent: `tests/mcp_servers/test_tools.py::test_mutual_ping_echo`.
  - Definition of done: round-trip succeeds before any real game logic is
    wired through.

- [x] **Pipeline sanity check on the 1×2 grid**
  - Priority: High
  - Status: done —
    `tests/mcp_servers/test_pipeline.py::test_dummy_message_travels_end_to_end_on_1x2_grid`
    drives one full sub-game through the tool-call chain on a 1×2 board and
    asserts the transcript is logged.
  - Definition of done: dummy message travels Client → tool call → MCP
    server → response, logged correctly.

- [x] **Wire up the full chain: orchestrator → LLM → tool-call decision →
  MCP server → engine update → result back to orchestrator**
  - Priority: High
  - Status: done, with an explicit scoping decision — `src/agents/orchestrator.py`
    wires the full mechanical chain (decision → `choose_action` tool call →
    MCP server → engine → result → next decision), but the decision step
    is `src/agents/policy_stub.py` (random legal action), **not** a real LLM
    call yet. Spending real API tokens on a random-walk placeholder before
    Phase 3 (strategy) and Phase 4 (NL dialogue) exist would be wasted
    spend; the plug point is isolated to one small module so swapping in the
    LLM later is a one-file change, not a rewire of the chain.
  - Definition of done: a single turn is driven entirely through this chain
    with no manual intervention — confirmed.

- [x] **Run a complete sub-game between the two agents on localhost**
  - Priority: High
  - Status: done — `run_subgame_via_mcp()` runs to a winner via the MCP
    chain; covered by `test_full_subgame_terminates_with_a_winner`.
  - Definition of done: one full sub-game completes autonomously with a
    readable transcript.

- [x] **Run a full 6-sub-game series locally and confirm totals match
  Table 1's scoring rules**
  - Priority: High
  - Status: done — `run_series_via_mcp()`; `test_full_series_totals_match_scoring_table`
    asserts the totals equal the sum of per-sub-game points, and each
    sub-game's points match the scoring table for its winner.
  - Definition of done: confirmed exactly, both by assertion and by hand on
    sample runs (e.g. 6/6 Cop wins → 120/30 totals on a 3×3 grid).

- [x] **Sanity progression: 1×2 → 2×3/3×2 → 3×4/4×3 → 5×5**
  - Priority: Medium
  - Status: done — ran a 6-sub-game series via the MCP chain at each grid
    size in the progression with the random placeholder policy; see the
    notes log below for the observations recorded at each stage.
  - Definition of done: each grid size run at least once, observations
    recorded.

---

## Phase 3 — Strategy / Decision-Making Mechanism

- [x] **Implement a heuristic strategy (Manhattan distance / decision
  tree) in `src/strategy/`**
  - Priority: High
  - Status: done — `src/strategy/heuristic.py`. Cop minimizes, Thief
    maximizes, Manhattan distance to the believed opponent position;
    exposed both as a `Policy` callable (local engine) and as a
    candidate-list callable (MCP orchestrator), now the orchestrator's
    default, replacing the Phase 2 random `policy_stub`.
  - Definition of done: confirmed — `tests/strategy/test_heuristic.py`
    asserts the Cop's pick always strictly decreases distance and the
    Thief's always strictly increases it (where a legal move allows).

- [x] **Implement Tabular Q-Learning, if pursued**
  - Priority: Medium
  - Status: done — `src/strategy/q_learning.py` (`QLearningAgent`) +
    `scripts/train_q_learning.py` (offline training loop against the
    local engine, not MCP). State = `(own_pos, opponent_pos)`; action =
    8 directions + `PLACE_BARRIER` (Cop only); reward = per-step
    Δ-Manhattan-distance + ±50 terminal capture bonus; Bellman update and
    epsilon-greedy with decay implemented; Q-tables persisted to
    `results/q_tables/{cop,thief}_qtable.json` after training.
  - Definition of done: confirmed — trained 4000 episodes on the
    configured 5×5 grid; see the calibration record in
    `docs/prd/strategy.md` and the raw curve in
    `results/q_tables/learning_curve.json`.

- [x] **Calibrate hyperparameters (α, γ, ε) and record the reasoning**
  - Priority: Medium
  - Status: done — recorded in `docs/prd/strategy.md` under
    "Implementation notes (Phase 3, done)": config defaults
    (α=0.1, γ=0.9, ε₀=0.2, decay=0.995) converged cleanly (Cop win-rate
    0.74 → 1.0 by ~episode 1300, no oscillation), so no retuning was
    needed; reasoning for keeping each default is written out there.
  - Definition of done: confirmed.

- [x] **Confirm the Cop's and Thief's strategies are unique and original
  implementations**
  - Priority: Low
  - Status: done — uniqueness note added to `docs/prd/strategy.md`; no
    code is shared with any partner group since the inter-group bonus
    (Phase 7) is still deferred.
  - Definition of done: confirmed for the current (no-bonus) scope; will
    be revisited if Phase 7 is picked back up.

- [x] **Unit tests for the Q-table update rule and the action-selection
  policy**
  - Priority: Medium
  - Status: done — `tests/strategy/test_q_learning.py`: hand-computed
    Bellman update assertions (including the zero-future-value terminal
    case), epsilon-greedy statistical test (8000 trials, observed rate
    within 0.025 of the analytically expected rate), save/load round-trip.
    Plus `tests/strategy/test_policy.py` for the heuristic/q_learning
    selector in `src/strategy/policy.py`. 52 tests total project-wide,
    95% coverage on `src/` (target ≥85%).
  - Definition of done: confirmed.

---

## Phase 4 — Natural-Language Dialogue & GUI

This is the heart of the assignment — treat it accordingly.

- [ ] **Replace any placeholder/rigid protocol with free natural-language
  messages generated by the LLM at every turn**
  - Priority: High
  - Status: not started
  - Definition of done: no numeric coordinates or fixed-format tokens
    appear anywhere in the inter-agent message payloads, verified by
    spot-checking real transcripts.

- [ ] **Have each agent describe intentions/observations/(optionally)
  deception in text, not coordinates**
  - Priority: High
  - Status: not started
  - Definition of done: messages read like genuine natural language, not
    templated fill-in-the-blank strings.

- [ ] **Belief update on receipt: parse the opponent's message, update an
  internal belief, feed it into the strategy module**
  - Priority: High
  - Status: not started
  - Definition of done: the belief-update step produces a different,
    reasonable output for at least a few distinct kinds of incoming
    message (vague, specific, contradictory, bluffing).

- [ ] **Handle partial observability via a visibility radius**
  - Priority: High
  - Status: not started
  - Definition of done: an agent only gets a direct, reliable observation
    of the opponent's position when within `observation.visibility_radius`;
    outside that radius it must reason from the NL channel alone.

- [ ] **Log the entire natural-language transcript per sub-game**
  - Priority: High
  - Status: not started
  - Definition of done: a full, human-readable transcript for every
    sub-game is written to `results/`/`logs/` — this is the primary
    evidence used for grading.

- [ ] **Write a qualitative review of ambiguous/nonsensical messages**
  - Priority: Medium
  - Status: not started
  - Definition of done: at least one concrete example, with how it was
    handled, recorded in the notes log below — not a generic statement
    that "some messages were ambiguous."

- [ ] **Build a real-time GUI showing the grid, agent positions, and
  barriers**
  - Priority: High
  - Status: not started
  - Definition of done: the GUI updates live as a sub-game plays out, not
    just a static end-of-game summary.

- [ ] **(Optional) Surface the belief state / Q-values in the GUI**
  - Priority: Low
  - Status: not started
  - Definition of done: if implemented, a viewer can see what each agent
    currently believes about the other's position, alongside the real
    state, for transparency.

- [ ] **Produce learning-curve graphs (if Q-Learning was implemented) and
  capture GUI screenshots**
  - Priority: Medium
  - Status: not started
  - Definition of done: both saved into `figures/`, ready to embed in the
    README and the technical report.

---

## Phase 5 — Cloud Deployment, Security & Automated Gmail Reporting

- [ ] **Deploy both MCP servers to the cloud**
  - Priority: High
  - Status: not started
  - Definition of done: Cop and Thief servers each have a stable, public
    HTTPS URL, reachable from outside your own network.

- [ ] **Implement token-based authentication with revocation support on
  each server**
  - Priority: High
  - Status: not started
  - Definition of done: a revoked token is provably rejected on the next
    request (test this explicitly, don't just assume it).

- [ ] **Confirm public HTTPS reachability, not blocked by any firewall**
  - Priority: High
  - Status: not started
  - Definition of done: a request from outside your home/work network
    succeeds; avoid testing from a restrictive organizational network,
    since that can produce false negatives.

- [ ] **Secure a local LLM via Ollama, if Approach 2 is used**
  - Priority: Low
  - Status: not applicable — Approach 1 (cloud API) is the chosen
    deployment approach per `docs/PLAN.md` ADR-1.

- [ ] **Confirm outbound-only calls, if Approach 3 (hybrid) is used**
  - Priority: Low
  - Status: not applicable — same reason as above.

- [ ] **Record the final two URLs (Cop, Thief) in `docs/ARCHITECTURE.md`**
  - Priority: High
  - Status: not started
  - Definition of done: both URLs present and current in that file, kept
    in sync if either server is ever redeployed.

- [ ] **Set up a Google Cloud project + OAuth Client Secret + token**
  - Priority: High
  - Status: not started
  - Definition of done: credentials obtained per the recorded walkthrough;
    paths stored in `.env`, the secret itself never committed to git.

- [ ] **Implement the reporting module so the Cop agent automatically
  sends a single summary email after all 6 sub-games**
  - Priority: High
  - Status: not started
  - Definition of done: the email is sent automatically, with no manual
    trigger, to `rmisegal+uoh26b@gmail.com`.

- [ ] **Email body = the Internal Game JSON only — no free text**
  - Priority: High
  - Status: not started
  - Definition of done: the body is exactly the JSON payload, nothing else,
    validated against the schema in `hw06_requirements.md` §11.1.

- [ ] **Handle Technical Loss: detect, void, and auto-re-run failed
  sub-games until 6 valid ones are recorded**
  - Priority: Medium
  - Status: not started
  - Definition of done: a simulated technical failure (e.g. a server made
    briefly unreachable) results in exactly one re-run of that sub-game,
    not a duplicated or corrupted series.

- [ ] **Write a test that mocks the Gmail call and asserts the JSON
  payload schema is correct**
  - Priority: Medium
  - Status: not started
  - Definition of done: the test fails if a required key is missing or
    mistyped, proving the schema check is actually meaningful.

---

## Phase 6 — Dec-POMDP Modeling, README & Technical Report

- [ ] **Formally define the Dec-POMDP tuple for this specific
  implementation**
  - Priority: High
  - Status: not started
  - Definition of done: every symbol in `⟨n, S, {Ai}, P, R, {Ωi}, O, γ⟩` is
    mapped to this project's actual state representation, action set, and
    reward table — not a copy of the generic textbook definition.

- [ ] **Write the orchestration-challenge analysis**
  - Priority: High
  - Status: not started
  - Definition of done: a concrete discussion of the real difficulties hit
    while managing free natural-language communication with no fixed
    protocol, how linguistic ambiguity was handled, and what was done to
    ensure mutual understanding between agents.

- [ ] **Write the deep-dive technical report under `reports/`**
  - Priority: High
  - Status: not started
  - Definition of done: covers architecture, the Dec-POMDP model, results
    across all sanity-check grid sizes, learning curves (if applicable),
    GUI screenshots, and cloud logs proving 6 autonomous natural-language
    sub-games.

- [ ] **Finalize `README.md` for an external reader**
  - Priority: High
  - Status: not started
  - Definition of done: installation instructions, usage instructions
    (local run / cloud run / bonus inter-group run), examples and demos,
    a configuration guide, code contribution guidelines, and license/
    attribution are all present, with graphs/tables/screenshots embedded
    and setup/run instructions that are genuinely copy-pasteable.

- [ ] **Explicitly answer the four required questions somewhere in the
  report**
  - Priority: High
  - Status: not started
  - Definition of done: how free-language orchestration differs from a
    rigid protocol; how partial observability shaped the belief-update
    logic; where the strategy's "skill ceiling" showed up; what the cloud
    deployment's security trade-offs were — each answered concretely, with
    evidence from this project's own runs.

---

## Phase 7 — Bonus: Inter-Group Cloud Competition

Currently deferred — not being pursued right now. Leaving the breakdown
here in case that changes.

- [ ] **Confirm the partner group's MCP server URLs and finalize the
  Inter-Group Bonus Game JSON schema together**
  - Priority: Low
  - Status: deferred

- [ ] **Play a full two-sided game — 6 sub-games (3 + 3, roles swapped)**
  - Priority: Low
  - Status: deferred

- [ ] **Capture full natural-language logs proving autonomy**
  - Priority: Low
  - Status: deferred

- [ ] **Both groups independently send emails with exactly matching
  results**
  - Priority: Low
  - Status: deferred
  - Definition of done (if revisited): results cross-checked between
    groups *before* either side sends anything — a mismatch disqualifies
    both groups for that series.

- [ ] **Compute and record the bonus score**
  - Priority: Low
  - Status: deferred

---

## Phase 8 — Final QA & Submission

- [ ] **Final QA gate against the §20.9 checklist**
  - Priority: High
  - Status: not started
  - Definition of done — each of the following confirmed individually:
    - Docs: PRD, architecture doc, README, API doc (MCP tool contracts),
      prompt book (`PROMPTS.md`) all present and accurate.
    - Code: modular structure, files ≤150 lines, comments + docstrings,
      consistent style.
    - Config: separated config files, `.env.example`, no secrets,
      `.gitignore` correct.
    - Testing: ≥85% coverage, edge cases, error handling, automated
      reports all covered.
    - Research: parameter exploration (grid size, hyperparameters),
      sensitivity analysis, an analysis notebook/script, graphs.
    - Visualization: quality graphs (learning curves), screenshots,
      architecture diagrams.
    - Costs: a token-usage table for LLM calls, with a short analysis and
      any optimization notes.
    - Extension: clearly marked extension points, extra examples, clean
      interfaces, if anything beyond spec was added.
    - General: clean git history, license, attribution, deployment notes.

- [ ] **Cross-check code quality specifically**
  - Priority: High
  - Status: not started
  - Definition of done: clear separation of responsibilities; comments
    explain *why*, not just *what*; docstrings on every function/class/
    module; descriptive names; short single-responsibility functions;
    no duplicated logic (DRY).

- [ ] **Cross-check the repo structure matches the target layout**
  - Priority: High
  - Status: not started
  - Definition of done: `src/`, `tests/`, `docs/`, `data/`, `results/`,
    `config/`, `figures/` cleanly separated by role, matching
    `docs/PLAN.md`.

- [ ] **Scrub all API keys / OAuth secrets from git history**
  - Priority: High
  - Status: not started
  - Definition of done: a fresh clone of the repo contains zero live
    secrets, anywhere in history, not just in the current working tree.

- [ ] **Submit via the standard submission space**
  - Priority: High
  - Status: not started
  - Definition of done: all mandatory steps submitted, plus the bonus if
    it ends up getting completed.

- [ ] **Reconfirm the submission deadline, and the HW05 extension if the
  bonus was submitted**
  - Priority: High
  - Status: not started

---

## Notes log

- 2026-06-23: Phase 0 repo skeleton, baseline files, config skeleton,
  `CONCEPTS.md`, `PRD.md`, `PLAN.md`, and the mini-PRDs under `docs/prd/`
  created. `PROMPTS.md`, `API.md`, and `ARCHITECTURE.md` drafted as
  skeletons to be filled in for real once Phase 2 starts. Confirmed with
  the user: submission-deadline confirmation and the inter-group bonus are
  both deferred for now — not blocking progress into Phase 1.
- This TODO file was rewritten from a table-based format to a checklist
  format for readability, with each task expanded to include its
  rationale and a concrete definition of done, per explicit feedback that
  the original was too thin and hard to read.
- 2026-06-23: Phase 2 implemented — `src/mcp_servers/` (session, factory,
  cop_server, thief_server, auth), `src/agents/` (policy_stub,
  orchestrator), `scripts/run_mcp_servers.py`, and
  `tests/mcp_servers/{test_tools,test_pipeline,test_auth}.py` (15 new tests,
  all passing; project-wide coverage 98%, target ≥85%). The project's own
  `.venv` had no dependencies installed yet (Phase 0's "create environment"
  item was still "not started") — installed `requirements.txt` into it
  before any of this could run.
- 2026-06-23: Sanity progression run via `run_series_via_mcp()` with the
  random placeholder policy (6 sub-games per grid, seed=99):
  - `(1,2)`: 6/6 Cop wins, every sub-game ends in 1 move. Smallest board
    leaves the Thief almost nowhere to go without colliding with the Cop —
    expected and matches the Phase 1 1×2 sanity test's spirit.
  - `(2,3)`, `(3,2)`: still 6/6 Cop wins, moves-to-capture ranged 1–6.
  - `(3,4)`, `(4,3)`: 6/6 Cop wins, moves-to-capture ranged 2–19 — more
    room lets some sub-games run much longer before the random walk
    collides.
  - `(5,5)`: 5/6 Cop wins, 1 Thief survival (the 25-move cap was hit) —
    totals 105/35.
  - **Observation worth flagging for Phase 3:** a uniformly random Thief
    is not actually "evading" anything — it wins only when its random walk
    happens to dodge the Cop for 25 moves, which gets more likely as the
    grid grows (consistent with the one survival appearing only at 5×5).
    The lopsided win rate here is an artifact of `policy_stub`'s randomness,
    not a property of the engine or the MCP wiring — don't read it as a
    balance problem to fix before Phase 3 lands a real strategy.
  - **Also confirms existing Phase 1 capture semantics carry through the
    MCP chain unchanged:** if the *Thief* moves onto the Cop's cell, that
    still scores as a Cop win (`Board.is_captured()` doesn't care which
    side moved last) — same as `src/engine/subgame.py`. Worth re-examining
    once real strategy/NL dialogue exist, since a bluffing Thief could
    plausibly want to avoid ever being adjacent to a stated Cop position,
    not just avoid moving onto it.
  - No technical failures, hangs, or hyperparameter issues at any grid
    size — there's no learning component yet (Phase 3), so "hyperparameter
    problems" don't apply at this stage.
- 2026-06-23: Phase 3 implemented — `src/strategy/{heuristic,q_learning,
  policy}.py`, `scripts/train_q_learning.py`, and
  `tests/strategy/{test_heuristic,test_q_learning,test_policy}.py` (15 new
  tests, all passing; project-wide 52 tests, 95% coverage, target ≥85%).
  `src/agents/orchestrator.py`'s default `policy_fn` switched from the
  Phase 2 random `policy_stub` to the new heuristic. Trained Q-tables for
  4000 episodes on the configured 5×5 grid — Cop win-rate rose from 0.74
  (episode 50) to 1.0 (by ~episode 1300, held through 4000) as epsilon
  decayed to its floor; full calibration record and reasoning in
  `docs/prd/strategy.md`. Cop dominance at this stage is consistent with
  the Phase 2 random-policy sanity progression (also Cop-favored on 5×5)
  and is expected to shift once Phase 4's partial observability and NL
  bluffing give the Thief tools the Cop can't see through — flagged there
  for re-measurement, not treated as a balance bug to fix now.
