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

- [x] **Create an isolated environment (e.g. `uv venv`) and install deps**
  - Priority: High
  - Owner: unassigned
  - Status: done — `.venv` created and `requirements.txt` installed
    (confirmed by the full test suite + the real LLM demo run, both
    passing/running cleanly against it).
  - Definition of done: confirmed; exact version pinning deferred to
    Phase 8 final QA.

- [x] **Populate `.env` from `.env.example`**
  - Priority: High
  - Owner: unassigned
  - Status: partially done — `ANTHROPIC_API_KEY` and the MCP auth tokens
    are populated and confirmed working (real demo run completed). Gmail
    OAuth credential paths still empty — that's a Phase 5 prerequisite,
    not needed yet.
  - Definition of done: LLM API key in place (done); Gmail OAuth paths
    deferred to Phase 5.

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

- [x] **Replace any placeholder/rigid protocol with free natural-language
  messages generated by the LLM at every turn**
  - Priority: High
  - Status: done — `src/agents/dialogue.py:generate_nl_message()` calls
    `src/agents/llm_client.py` (Anthropic, paid tier) every turn when `llm_client` is
    passed into the orchestrator; falls back to the old fixed template only
    on a hard API failure (graceful degradation, not the normal path).
  - Definition of done: confirmed in code (system prompts explicitly forbid
    raw coordinates); real-transcript spot-check is pending the user's own
    run with their API key (`scripts/run_llm_demo.py`) — flagged in the
    notes log below.

- [x] **Have each agent describe intentions/observations/(optionally)
  deception in text, not coordinates**
  - Priority: High
  - Status: done — `src/agents/dialogue.py:choose_deception_level()` picks
    "truthful"/"vague"/"mislead" per turn (Thief bluffs more than Cop, see
    `docs/PROMPTS.md` §2.4), fed into the system prompt alongside the
    agent's belief and intended action.
  - Definition of done: confirmed by `tests/agents/test_dialogue.py`; real
    qualitative read of genuine model output is pending the user's run.

- [x] **Belief update on receipt: parse the opponent's message, update an
  internal belief, feed it into the strategy module**
  - Priority: High
  - Status: done — `src/agents/belief.py:update_belief()` (direct
    observation always overrides the NL-derived estimate) +
    `make_belief_board()` feeds the believed opponent position into the
    existing `src/strategy/` modules unchanged via a proxy `Board`.
  - Definition of done: confirmed — `tests/agents/test_belief.py` covers
    vague/no-information/direct-observation-override cases distinctly.

- [x] **Handle partial observability via a visibility radius**
  - Priority: High
  - Status: done — new `observe_opponent` MCP tool
    (`src/mcp_servers/factory.py`), gated by `session.visibility_radius`
    (from `config.yaml: observation.visibility_radius`); documented in
    `docs/API.md`.
  - Definition of done: confirmed —
    `tests/mcp_servers/test_tools.py::test_observe_opponent_*`.

- [x] **Log the entire natural-language transcript per sub-game**
  - Priority: High
  - Status: done — `src/engine/results.py:save_transcript_log()` writes a
    human-readable `.txt` per sub-game to `results/transcripts/`, called
    from `scripts/run_llm_demo.py` after each sub-game.
  - Definition of done: confirmed by
    `tests/engine/test_results.py::test_save_transcript_log_writes_readable_text`;
    real transcripts from an actual run are pending the user's API key.

- [x] **Write a qualitative review of ambiguous/nonsensical messages**
  - Priority: Medium
  - Status: done — concrete example pulled from a real run, recorded in
    the notes log below.
  - Definition of done: confirmed.

- [x] **Build a real-time GUI showing the grid, agent positions, and
  barriers**
  - Priority: High
  - Status: done — `src/gui/app.py` (Streamlit), polling
    `src/gui/state_writer.py`'s JSON snapshot file, written by the
    orchestrator's `on_turn` callback after every turn.
  - Definition of done: confirmed by code review and
    `tests/gui/test_state_writer.py`; an actual browser screenshot for the
    report is pending the user running `scripts/run_llm_demo.py` +
    `streamlit run src/gui/app.py` themselves (I have no display in this
    environment).

- [x] **(Optional) Surface the belief state / Q-values in the GUI**
  - Priority: Low
  - Status: done — the GUI's per-agent panel shows the live belief note +
    confidence alongside the true grid state.
  - Definition of done: confirmed by code review.

- [x] **Produce learning-curve graphs (if Q-Learning was implemented) and
  capture GUI screenshots**
  - Priority: Medium
  - Status: done — `scripts/plot_learning_curve.py` renders
    `results/q_tables/learning_curve.json` to `figures/learning_curve.png`;
    GUI screenshot captured by the user from the live Streamlit app after
    the real demo run (see notes log).
  - Definition of done: confirmed.

---

## Phase 5 — Cloud Deployment, Security & Automated Gmail Reporting

- [x] **Deploy both MCP servers to the cloud**
  - Priority: High
  - Status: done — two independent Render web services,
    `cop-mcp-server` and `thief-mcp-server-u04c`, each running
    `scripts/run_mcp_servers.py` with `MCP_SERVER_ROLE=cop`/`thief`.
  - Definition of done: confirmed — `https://cop-mcp-server.onrender.com/mcp`
    and `https://thief-mcp-server-u04c.onrender.com/mcp` both stable,
    public HTTPS URLs.

- [x] **Implement token-based authentication with revocation support on
  each server**
  - Priority: High
  - Status: done — `src/mcp_servers/auth.py:RevocableTokenVerifier` checks
    an on-disk revocation list (`REVOKED_TOKENS_PATH`) fresh on every
    `verify_token` call; `revoke_token()` appends to that list. No server
    restart needed for a revocation to take effect.
  - Definition of done: confirmed —
    `tests/mcp_servers/test_auth.py::test_revoked_token_is_rejected_on_next_request_without_restart`
    revokes a token mid-session (server stays running) and asserts the very
    next request with that token fails.

- [x] **Confirm public HTTPS reachability, not blocked by any firewall**
  - Priority: High
  - Status: done — `scripts/check_cloud_reachability.py` confirmed both
    URLs respond to a real `ping` tool call from outside the deployment
    network; a full real 6-sub-game LLM-driven series was also played
    against both servers end to end via `run_llm_demo.py`'s remote-endpoint
    mode (totals: Cop 90, Thief 40), proving the reachability holds up
    under sustained real traffic, not just a single ping.
  - Definition of done: confirmed.

- [ ] **Secure a local LLM via Ollama, if Approach 2 is used**
  - Priority: Low
  - Status: not applicable — Approach 1 (cloud API) is the chosen
    deployment approach per `docs/PLAN.md` ADR-1.

- [ ] **Confirm outbound-only calls, if Approach 3 (hybrid) is used**
  - Priority: Low
  - Status: not applicable — same reason as above.

- [x] **Record the final two URLs (Cop, Thief) in `docs/ARCHITECTURE.md`**
  - Priority: High
  - Status: done — both URLs recorded in `docs/ARCHITECTURE.md`'s cloud
    deployment table, also mirrored in `config.yaml: mcp.{cop,thief}_mcp_url`.
  - Definition of done: confirmed.

- [x] **Set up a Google Cloud project + OAuth Client Secret + token**
  - Priority: High
  - Status: done — Google Cloud project created, Gmail API enabled, OAuth
    consent screen configured (External, `gmail.send` scope, test user
    added), Desktop-app OAuth client created;
    `secrets/client_secret.json` saved, `GMAIL_CLIENT_SECRET_PATH`/
    `GMAIL_TOKEN_PATH` set in `.env`. `secrets/` added to `.gitignore` as
    a blanket rule (confirmed via `git check-ignore -v`, neither file is
    tracked).
  - Definition of done: confirmed — first real send triggered the
    interactive consent flow once; `secrets/token.json` now cached, every
    later send is silent (confirmed by the redo below).

- [x] **Implement the reporting module so the Cop agent automatically
  sends a single summary email after all 6 sub-games**
  - Priority: High
  - Status: done — `src/reporting/{schema,game_report,gmail_sender}.py`;
    `scripts/run_llm_demo.py` calls `build_internal_game_json` ->
    `validate_internal_game_json` -> `send_report` automatically right
    after `run_series_via_mcp` returns (no separate manual trigger script),
    skipping with a clear message if `config.yaml:
    reporting.send_on_completion` is false or Gmail OAuth env vars aren't
    set.
  - Definition of done: confirmed end to end — a real 6-sub-game series
    completed (totals Cop 90/Thief 40) and the Internal Game JSON was
    emailed successfully (Gmail message id `19efdcd03b396e88`) to a test
    recipient (`REPORT_RECIPIENT_OVERRIDE`), schema-verified against the
    actual PDF spec (hw06 source PDF, S9.1) field-by-field.

- [x] **Email body = the Internal Game JSON only — no free text**
  - Priority: High
  - Status: done — `gmail_sender.send_report` builds the email via
    `email.mime.text.MIMEText(json.dumps(payload, indent=2))` with no other
    content; schema enforced by `src/reporting/schema.py` before send.
  - Definition of done: confirmed —
    `tests/reporting/test_gmail_sender.py::test_send_report_body_is_exactly_the_json_payload`
    decodes the actual raw MIME message sent to the (mocked) Gmail API and
    asserts the body round-trips through `json.loads` to the exact payload.

- [x] **Handle Technical Loss: detect, void, and auto-re-run failed
  sub-games until 6 valid ones are recorded**
  - Priority: Medium
  - Status: done — `src/agents/orchestrator.py
    :_run_subgame_with_technical_loss_retry`; any exception out of
    `run_subgame_via_mcp` (MCP unreachable, malformed response, etc. — a
    normal game outcome never raises) voids that attempt and retries the
    same sub-game in place, up to `max_technical_retries` (default 2);
    `run_series_via_mcp`'s return value now also carries
    `technical_losses` (a log of every voided attempt, for grading
    evidence) and still always ends with exactly `num_games` sub-games.
  - Definition of done: confirmed —
    `tests/agents/test_orchestrator.py::test_technical_loss_is_voided_and_retried_without_corrupting_the_series`
    injects exactly one simulated failure and asserts the series ends with
    the right sub-game count and exactly one logged retry, not a
    duplicate/gap; a second test confirms it gives up with a clear error
    after exhausting retries rather than hanging forever.

- [x] **Write a test that mocks the Gmail call and asserts the JSON
  payload schema is correct**
  - Priority: Medium
  - Status: done — `tests/reporting/test_schema.py` (5 tests: well-formed
    payload passes; missing key, wrong type, missing totals side, and
    non-int totals value are each individually rejected with a clear
    error) plus `tests/reporting/test_game_report.py` (assembled payload
    passes the same schema check) and `tests/reporting/test_gmail_sender.py`
    (mocks `googleapiclient.discovery.build` and the OAuth credential
    loading, never touches the real network).
  - Definition of done: confirmed — each schema test fails if its specific
    corruption isn't caught, proving the check is meaningful rather than a
    rubber stamp.

---

## Phase 6 — Dec-POMDP Modeling, README & Technical Report

- [x] **Formally define the Dec-POMDP tuple for this specific
  implementation**
  - Priority: High
  - Status: done — `reports/technical_report.md` §2; every symbol mapped to
    real code (`Board`, `observe_opponent`, `belief.py`, `config.yaml`
    scoring/gamma), including an explicit note on where this project's
    two-channel observation function (exact-but-rare visibility radius vs.
    always-available-but-adversarial NL) departs from the textbook
    single-channel `O`.
  - Definition of done: confirmed.

- [x] **Write the orchestration-challenge analysis**
  - Priority: High
  - Status: done — `reports/technical_report.md` §3, three concrete
    difficulties pulled from the real transcripts (bluffing
    indistinguishable from model error at the text level, vagueness as a
    first-class non-error outcome, belief-default behavior visibly shaping
    physical movement), each with a transcript quote, not a generic
    discussion.
  - Definition of done: confirmed.

- [x] **Write the deep-dive technical report under `reports/`**
  - Priority: High
  - Status: done — `reports/technical_report.md` covers architecture, the
    Dec-POMDP model, results across the full sanity-check progression
    (random policy → heuristic/Q-learning → real local LLM run → real
    cloud LLM run), the learning curve, and cloud deployment evidence
    (§7: both Render URLs, `check_cloud_reachability.py` confirmation,
    a full cloud-driven 6-sub-game series — Cop 90/Thief 40 — and a real
    Gmail send, message id `19efdcd03b396e88`). GUI screenshot now embedded
    in §6 (`figures/gui_screenshot.png`, captured by the user from the
    leftover `results/live_state.json` snapshot — no need to re-run the
    series, the GUI just polls whatever's on disk).
  - Definition of done: confirmed, fully done.

- [x] **Finalize `README.md` for an external reader**
  - Priority: High
  - Status: done — installation, local-run usage, cloud-run usage (with an
    explicit status note that reachability/Gmail OAuth confirmation is
    still pending, per Phase 5), offline Q-learning training, a
    configuration-guide table mapping every `config.yaml` section, a tests
    section, and contribution guidelines all present; setup/run commands
    are copy-pasteable.
  - Definition of done: confirmed, modulo embedding the still-pending GUI
    screenshot once captured.

- [x] **Explicitly answer the four required questions somewhere in the
  report**
  - Priority: High
  - Status: done — all four fully answered in `reports/technical_report.md`
    §8, each with concrete evidence from real runs: free-NL-vs-rigid-
    protocol and partial-observability (local transcript evidence, §3);
    skill-ceiling (the Q-learning-vs-heuristic distinction, §5); cloud
    security trade-offs (token revocation design + Render's TLS
    termination + confirmed-gitignored OAuth secrets, now backed by the
    real cloud deployment evidence in §7 rather than a design-only answer).
  - Definition of done: confirmed.

---

## Phase 7 — Bonus: Inter-Group Cloud Competition

Currently deferred — no partner group identified, not being actively
pursued. Code scaffolding now exists and is tested (2026-06-25, see notes
log) so this is ready to use the moment a partner group shows up; the
checklist below stays unstarted/deferred until that happens, since none
of it can actually be exercised against a real second deployment yet.

- [ ] **Confirm the partner group's MCP server URLs and finalize the
  Inter-Group Bonus Game JSON schema together**
  - Priority: Low
  - Status: deferred — schema side is already built and tested
    (`src/reporting/bonus_schema.py`, matches hw06_requirements.md §11.2
    exactly); what's missing is an actual partner group to confirm it
    with.

- [ ] **Play a full two-sided game — 6 sub-games (3 + 3, roles swapped)**
  - Priority: Low
  - Status: deferred — `scripts/run_bonus_series.py` runs exactly this,
    but as a **peer protocol both groups run simultaneously**
    (`src.agents.bonus_peer*`), each deciding only its own agent's moves
    — not one side driving both, which was the original (corrected)
    design; see `docs/prd/bonus-inter-group.md`'s "Architecture" section.
    Blocked on having a partner group's real URLs/tokens to point it at.

- [ ] **Capture full natural-language logs proving autonomy**
  - Priority: Low
  - Status: deferred — each side's own peer process logs its own
    transcript per sub-game the same way the base game does; nothing
    extra to build, just needs a real cross-group run to produce them.

- [ ] **Both groups independently send emails with exactly matching
  results**
  - Priority: Low
  - Status: deferred — see `docs/prd/bonus-inter-group.md`'s "Algorithm /
    process" for the concrete coordination model: both sides now run the
    full script themselves and independently arrive at the same result
    (proven in-process by `tests/agents/test_bonus_peer.py`), then compare
    before either sends. `scripts/send_bonus_report.py` remains as a
    fallback for a side sending an already-agreed payload it didn't
    generate itself.
  - Definition of done (if revisited): results cross-checked between
    groups *before* either side sends anything — a mismatch disqualifies
    both groups for that series.

- [ ] **Compute and record the bonus score**
  - Priority: Low
  - Status: deferred — `src/reporting/bonus_scoring.py` implements the
    10/7/5 rule and multi-partner averaging already, tested
    (`tests/reporting/test_bonus_scoring.py`); just needs a real result to
    compute from.

---

## Phase 8 — Final QA & Submission

- [x] **Final QA gate against the §20.9 checklist**
  - Priority: High
  - Status: done — verified individually:
    - Docs: PRD, `ARCHITECTURE.md`, README, `API.md`, `PROMPTS.md` all
      present and accurate against the current code.
    - Code: modular, every `src/`/`scripts/` file ≤150 lines (largest is
      `scripts/run_bonus_series.py` at 142), every module has a docstring,
      consistent style throughout.
    - Config: `config/config.yaml` + `.env.example` separated, no secrets
      tracked (`git ls-files` clean, `git log --all -- .env secrets/
      '*token.json' '*client_secret*.json'` empty), `.gitignore` covers
      `.env`, `secrets/`, token/credential files, and runtime artifacts.
    - Testing: 133 tests passing, 92% coverage (target ≥85%); edge cases
      (technical-loss retry, draw retry, revocation, schema corruption)
      and error handling all have dedicated tests.
    - Research: grid-size sanity progression (Phase 2), Q-learning
      hyperparameter calibration (`docs/prd/strategy.md`), and the
      full-vs-partial-observability Q-learning comparison (ADR-6) all
      recorded with reasoning, not just results.
    - Visualization: `figures/learning_curve.png`, `figures/
      gui_screenshot.png`, C4 + sequence diagrams in `docs/PLAN.md`, all
      embedded in README/technical report.
    - Costs: added `reports/technical_report.md` §9 — a token-usage table
      grounded in real on-disk transcripts and configured `max_tokens`
      ceilings (this project never instrumented per-call `usage` counters,
      so it's an honest grounded estimate, flagged as such, not a literal
      billing export), plus the optimization notes actually applied.
    - Extension: Phase 7 bonus scaffolding is explicitly marked
      not-mandatory in every file's docstring; ADR-6's sentinel design and
      ADR-7/8 are documented extension-point decisions.
    - General: license attribution filled in (was a placeholder "Team"),
      deployment notes in `docs/ARCHITECTURE.md`; git history scrubbed
      (see below).

- [x] **Cross-check code quality specifically**
  - Priority: High
  - Status: done — every `src/` module has a docstring (verified by
    script, zero misses); no file exceeds 150 lines; the Phase 7 bonus
    modules (newest, least-reviewed code) spot-checked individually and
    each carries a docstring explaining its role and why it was split out.
    No new DRY violations found.

- [x] **Cross-check the repo structure matches the target layout**
  - Priority: High
  - Status: done — `src/`, `tests/`, `docs/`, `data/`, `results/`,
    `config/`, `figures/`, `reports/`, `scripts/` all present and cleanly
    separated by role, matching `docs/PLAN.md`.

- [x] **Scrub all API keys / OAuth secrets from git history**
  - Priority: High
  - Status: done — confirmed via `git log --all --full-history -- .env
    secrets/ '*token.json' '*client_secret*.json'` (empty — never tracked,
    ever) and `git grep` for Anthropic/Google API-key shaped strings
    across all tracked files (no matches). `secrets/`, `.env`, and
    `bonus_partner_notes*.md` are gitignored and untracked.

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
- 2026-06-24: Phase 4 implemented — `src/agents/{llm_client,belief,
  dialogue}.py`, `src/gui/{state_writer,app}.py`, `scripts/run_llm_demo.py`,
  and a new `observe_opponent` MCP tool (`src/mcp_servers/factory.py`,
  documented in `docs/API.md`). 25 new tests (mirrored under
  `tests/{agents,gui}/`), all LLM calls mocked — project-wide now 77 tests,
  88% coverage, target ≥85%. Key design choice: rather than rewriting the
  Phase 3 strategy modules to accept a belief, the orchestrator builds a
  proxy `Board` (`make_belief_board`) with the opponent's position replaced
  by the current belief estimate (own position/barriers stay true) and
  feeds that into the unchanged `heuristic_candidate_actions`/Q-learning
  candidate builders — keeps strategy code belief-agnostic per
  `docs/PROMPTS.md`'s separation-of-concerns rule, and avoids touching the
  15 passing Phase 3 strategy tests.
  **Not yet done, explicitly deferred to the user:** no real LLM call has
  been made in this session (no `ANTHROPIC_API_KEY` available here) — the
  qualitative review of an ambiguous message, a real browser screenshot of
  the GUI, and the learning-curve figure render to `figures/` all need the
  user to run `scripts/run_llm_demo.py` (after populating `.env`) and
  `streamlit run src/gui/app.py` themselves. Flagged as the immediate next
  step once a key is available.
- 2026-06-24: Switched LLM provider from Anthropic to Groq, per request —
  `src/agents/llm_client.py` now wraps `groq.Groq` (chat-completions
  shape: `messages=[{"role": "system"|"user", ...}]`,
  `response.choices[0].message.content`, instead of Anthropic's
  `system=`/`response.content[0].text`); `config.yaml: llm.{provider,
  model}` and `.env.example` updated (`GROQ_API_KEY`, model
  `llama-3.1-8b-instant` — Groq's cheap/fast tier, same reasoning as the
  earlier Haiku pick: hundreds of calls per series). All 5
  `tests/agents/test_llm_client.py` tests updated to mock `groq.Groq`/
  `groq.APIError` instead of the Anthropic equivalents; `belief.py`/
  `dialogue.py`/`orchestrator.py` were untouched since they only depend on
  `LLMClient`'s `generate_text`/`generate_json` interface, not the
  underlying SDK.
- 2026-06-24: First real run attempt (Groq, `llama-3.1-8b-instant`) on the
  configured 5x5 grid stalled badly — ~3-7 minutes per move instead of
  seconds. Root cause, confirmed by inspecting `x-ratelimit-*` response
  headers directly: this model's free tier caps at 6,000 tokens/minute,
  and our ~2 LLM calls/turn (belief-parse + message) at ~280 tokens each
  exhausts that budget within a handful of rounds; the actual reset window
  is only a few seconds, but the Groq SDK's own internal retry (default
  `max_retries=2`, exponential backoff) stacked with our own outer
  retry-once loop compounded into multi-minute stalls. First mitigation
  (lower `max_tokens`, `max_retries=1`) helped but didn't remove the
  single-model ceiling. **Switched provider again, to OpenRouter** (still
  per user request, to get a real backup-model mechanism rather than just
  tuning retries): `src/agents/llm_client.py` now wraps the `openai` SDK
  pointed at OpenRouter's base URL, with `config.yaml: llm.model` (primary)
  + `llm.fallback_models` (ordered fallback list) — each OpenRouter model
  has its own independent rate-limit bucket, so falling forward to the next
  model on an `APIError` multiplies effective throughput instead of waiting
  out one model's quota. Primary + 3 fallbacks are all free-tier models
  (`meta-llama/llama-3.2-3b-instruct:free` first, since it's the
  smallest/fastest). `tests/agents/test_llm_client.py` rewritten (7 tests,
  including an explicit fallback-rotation test); `belief.py`/`dialogue.py`/
  `orchestrator.py` untouched again, same reason as above.
  On retesting, OpenRouter's free-tier models turned out to be rate-limited
  *upstream in a global pool shared across all OpenRouter users* — all 4
  configured free models (and several others probed) returned 429s
  unrelated to our own usage; availability fluctuates independent of
  anything in this codebase. **Switched a third time, to the direct
  Anthropic API on a paid key** — discussed cost with the user first: full
  per-run token volume is small (~100-200K tokens), and the whole
  assignment's expected ~8-12 runs (sanity stages + cloud run + possible
  bonus) totals an estimated $1-3 even at Haiku pricing, so a paid key's
  dedicated (non-shared) capacity was judged worth it over continuing to
  chase free-tier availability. `src/agents/llm_client.py` reverted to the
  single-model Anthropic wrapper (no fallback-list complexity needed — a
  paid key isn't subject to the shared-pool contention that caused the
  previous two switches); `requirements.txt`/`config.yaml`/`.env.example`
  reverted to `anthropic`/`claude-haiku-4-5-20251001`;
  `scripts/check_openrouter_models.py` deleted (no longer relevant).
  `tests/agents/test_llm_client.py` reverted to mocking `anthropic.Anthropic`.
- 2026-06-24: First real run on the Anthropic key hung indefinitely partway
  through sub-game 1 (raced through the first 12 moves in ~20s, then froze
  completely with no progress for 7+ minutes). Root cause: the Anthropic
  SDK's default request timeout is 10 minutes — far too long for a per-turn
  call in a real-time loop, so a single slow/stuck request just hangs the
  whole series rather than failing over to the fixed-template fallback.
  Fix: added an explicit `timeout=30.0` to the `Anthropic(...)` client
  construction in `src/agents/llm_client.py`. Restarted — completed cleanly
  end to end after that, no further hangs (pace was variable, roughly
  30s-2min/move, total wall time a bit over an hour for all 6 sub-games;
  this variability is normal API latency/load, not a bug).
- 2026-06-24: **First complete real 6-sub-game LLM-driven series**, 5x5
  grid, `claude-haiku-4-5-20251001`. Totals: **Cop 75, Thief 45** (Cop won
  sub-games 2/3/4 by capture in 2/12/11 moves; Thief won sub-games 1/5/6 by
  surviving the full 25-move cap). Transcripts in
  `results/transcripts/subgame_5x5_0{1-6}_*.txt`.
  **Qualitative review of ambiguous/deceptive messages** (Phase 4 success
  criterion): in sub-game 1, the Thief's NL messages frequently
  contradicted its own logged action — e.g. Turn 33: message "I'm heading
  south toward the river district, nowhere near the north end." while the
  actual action was `{'type': 'move', 'direction': 'N'}`. This is the
  deception mechanism working as designed (`choose_deception_level`
  picked "mislead" for the Thief that turn), not a model error — and per
  `docs/prd/nl-dialogue.md`'s edge-case handling, the orchestrator logs
  this mismatch rather than trying to "correct" it. By contrast, in
  sub-game 2 the Cop's belief was "high confidence" (Thief within
  visibility radius) and its message — "I can see you clearly. I'm moving
  southeast now." — was accurate; it captured the Thief two turns later.
  Across all 6 transcripts, almost every message that the belief-update
  LLM call classified as "no reliable information" was a genuinely vague
  spatial description (e.g. "I'm somewhere in the middle of the grid,
  heading toward the edges") rather than a parse failure — the belief
  module's confidence labeling tracked message vagueness correctly, not
  just API/JSON failures.
  **Secondary observation, flagged for the strategy/heuristic discussion in
  the technical report, not a bug to fix now:** the Thief's actual
  movement oscillated almost entirely between two cells, `(0,0)` and
  `(1,0)`, for most of sub-games where its belief stayed at "no
  information." This is the heuristic strategy's fallback-to-grid-center
  behavior (`make_belief_board` defaults the unknown opponent position to
  `(2,2)` on a 5x5 grid) combined with the Thief's "maximize distance from
  believed opponent" rule, which both point it toward the same two
  edge cells repeatedly when there is no real positional information —
  worth discussing in the orchestration-challenges write-up (Phase 6) as a
  concrete example of how belief uncertainty shapes physical behavior.
- 2026-06-24: Phase 5 (partial) — token revocation support implemented.
  `src/mcp_servers/auth.py`'s `StaticTokenVerifier` (FastMCP's built-in,
  construction-time-only) replaced with a new `RevocableTokenVerifier`
  (subclasses FastMCP's `TokenVerifier` base) that re-reads an on-disk
  revocation list (`REVOKED_TOKENS_PATH`, default
  `data/revoked_tokens.json`) fresh on every `verify_token` call — so
  `revoke_token(token)` takes effect on the very next request, no server
  restart required (the previous comment in that file said revocation
  meant restarting, which the new requirements doc reading flagged as not
  good enough: "a revoked token is provably rejected on the next request").
  New test `tests/mcp_servers/test_auth.py::
  test_revoked_token_is_rejected_on_next_request_without_restart` keeps one
  real HTTP server running throughout, makes a successful call, revokes the
  token, then asserts the next call with that same token fails — proving
  the "no restart" property rather than just asserting the revocation list
  is checked. `docs/API.md` and `.env.example` updated to document
  `REVOKED_TOKENS_PATH`. 79 tests total project-wide, all passing.
  **Remaining Phase 5 items deferred for now, per explicit user scope
  decision:** cloud deployment of both MCP servers, public-HTTPS
  reachability confirmation, recording the deployed URLs in
  `docs/ARCHITECTURE.md`, Google Cloud OAuth setup, the Gmail reporting
  module + Internal-Game-JSON schema validation/test, and Technical-Loss
  detection/auto-re-run. Not started.
- 2026-06-24: Phase 5 finished, except the two items that require you to
  click through external interfaces by hand (flagged below — everything
  codeable is done):
  - **Reporting module** — new `src/reporting/` package: `schema.py`
    validates the Internal Game JSON (hw06_requirements.md S11.1: required
    keys, types, and a `totals.{cop,thief}` int check) before anything is
    sent; `game_report.py` assembles that exact payload from a
    `run_series_via_mcp`/`run_game_series` result plus a new
    `config.yaml: group.{group_name,students,github_repo}` section (added
    with empty placeholders — fill these in before a real send);
    `gmail_sender.py` sends it via the Gmail API (`googleapiclient` +
    `google-auth-oauthlib`, all already in `requirements.txt` from Phase
    0), body = `MIMEText(json.dumps(payload, indent=2))` only, no prose.
    OAuth token loading (`_load_credentials`) caches/refreshes a token at
    `GMAIL_TOKEN_PATH` and only falls back to the interactive
    `InstalledAppFlow.run_local_server` consent flow when no cached token
    exists — so once you've done that once, every later send is silent.
  - **Wired into the one trigger point** — `scripts/run_llm_demo.py` now
    calls `build_internal_game_json` -> `validate_internal_game_json` ->
    `send_report` automatically right after the series completes (matching
    "the Cop agent automatically triggers... after all 6 sub-games", since
    this script *is* the Cop-and-Thief series runner); it skips reporting
    with a clear printed message if `GMAIL_CLIENT_SECRET_PATH`/
    `GMAIL_TOKEN_PATH` aren't set yet, so the script still works as a pure
    local/cloud demo before OAuth setup is done.
  - **Technical Loss handling** — `src/agents/orchestrator.py` gained
    `_run_subgame_with_technical_loss_retry`: any exception out of
    `run_subgame_via_mcp` (the normal "no legal action" case already
    returns a structured result rather than raising, so any raised
    exception here really does mean an infrastructure fault) voids that
    attempt and retries the *same* sub-game in place, up to
    `max_technical_retries` (default 2, new kwarg on `run_series_via_mcp`).
    The series return value gained a `technical_losses` list logging every
    voided attempt (sub-game index, attempt number, failure reason) as
    grading evidence, and still always ends with exactly `num_games` valid
    sub-games — never a duplicate or a gap.
  - **Tests** — 14 new tests: `tests/reporting/{test_schema,
    test_game_report,test_gmail_sender}.py` (12 — schema edge cases,
    payload assembly, and Gmail send with the API call + OAuth credential
    loading both mocked, asserting the exact decoded MIME body round-trips
    to the payload via `json.loads`) and two in
    `tests/agents/test_orchestrator.py` (one injects exactly one simulated
    technical failure and asserts the series still ends with the right
    sub-game count and exactly one logged retry; the other confirms it
    gives up with a clear `RuntimeError` instead of hanging forever once
    retries are exhausted). 93 tests total project-wide, 89% coverage
    (target ≥85%), `src/reporting/` itself at 100%.
  - **Explicitly NOT done — needs you, not code:** (1) deploying both MCP
    servers to a cloud host and confirming public HTTPS reachability —
    pick a platform, point it at `scripts/run_mcp_servers.py`, then fill
    the resulting URLs into `config.yaml: mcp.{cop,thief}_mcp_url` and
    `docs/ARCHITECTURE.md`; (2) the Google Cloud project + OAuth consent
    screen + client secret download (the recorded walkthrough) — once you
    have `GMAIL_CLIENT_SECRET_PATH` pointing at that file, the *first* real
    `run_llm_demo.py` run will open a one-time browser consent prompt via
    `InstalledAppFlow`, then cache a token and never prompt again. Also
    fill in `config.yaml: group.*` with your real group name/students/repo
    URL before that first real send, since it's currently empty
    placeholders.
- 2026-06-24: **Architecture fix, found while planning the deployment
  instructions above:** the two MCP servers shared one in-memory
  `GameSession` object (`src/mcp_servers/session.py`), which only worked
  because both ran in the same process. That silently broke the "two
  independent servers" requirement the moment they'd be deployed
  separately, and made the user's stated Phase 7 bonus goal (their Cop
  talking to a totally independently-deployed partner group's Thief)
  impossible outright. Per the user's explicit choice (real separation now
  rather than deferring to Phase 7), redesigned before doing any cloud
  deployment — see `docs/PLAN.md` ADR-5 for the full rationale.
  - `GameSession` -> `AgentSession` (`src/mcp_servers/session.py`): each
    server now owns only its own position, its own barrier set, and its
    own inbox. Nothing shared with the opponent's server.
  - `src/mcp_servers/factory.py`: `choose_action` no longer reports
    `captured` (a server can't know the opponent's position); two new
    tools — `receive_message` (orchestrator-relayed delivery, replacing
    `send_message` writing directly into the opponent's inbox) and
    `sync_barriers` (orchestrator pushes the Cop's barriers to the
    Thief's server, since barriers block both agents but only the Cop's
    own server learns about a new one directly); `observe_opponent` now
    takes an `opponent_position` parameter supplied by the caller instead
    of reading a shared board.
  - `src/agents/orchestrator.py`: now keeps its own `Board` mirror
    (`src/engine/board.py`, reused as-is) as the sole ground truth —
    applies each server-validated action to it directly, computes capture
    from it, and feeds it to the unchanged Phase 3/4 belief/strategy code
    exactly as before (`make_belief_board`/`heuristic_candidate_actions`
    take a `Board`, so none of that code needed to change). Also now
    explicitly relays messages (`_relay_turn`) and barrier syncs between
    the two independent server sessions.
  - `scripts/run_mcp_servers.py`: now supports two modes — local dev
    (both servers in one process, unchanged from before, just for a quick
    ping/echo check) and a new `MCP_SERVER_ROLE=cop|thief` cloud mode that
    starts only one server bound to `0.0.0.0:$PORT`, so the same script
    deploys as two genuinely separate services.
  - `docs/API.md` and `docs/PLAN.md` (Container diagram, sequence diagram,
    new ADR-5) updated to match.
  - Tests: `tests/mcp_servers/test_tools.py` rewritten for two independent
    sessions plus new coverage for `receive_message`/`sync_barriers`/the
    parameterized `observe_opponent`; `test_auth.py` updated to build an
    `AgentSession`. `tests/mcp_servers/test_pipeline.py` and
    `tests/agents/test_orchestrator.py` needed **no changes** — the public
    `run_subgame_via_mcp`/`run_series_via_mcp` signatures and return
    shapes were preserved exactly, which is exactly the point of keeping
    this an internal refactor. 97 tests total project-wide, all passing,
    89% coverage (target ≥85%).
- 2026-06-25: Phase 6 done as far as possible without Phase 5 finished, per
  explicit user request (cloud deployment to Render + Gmail API are being
  set up in parallel, outside this session). Verified current state first:
  re-ran the full suite (99 tests passing, 89% coverage — a couple of tests
  had crept in since the 97/89% note above, no regressions) and confirmed
  `config/config.yaml` already has real Render URLs for both MCP servers,
  though reachability and the Gmail OAuth send are not yet confirmed from
  this session. New `reports/technical_report.md`: architecture summary,
  the Dec-POMDP tuple mapped to real code (§2, including an explicit note
  on the two-channel observation function — exact-but-rare visibility
  radius vs. always-on-but-adversarial NL — departing from the textbook
  single-channel `O`), the orchestration-challenge analysis (§3, three
  concrete transcript-backed difficulties: bluffing vs. model-error
  indistinguishability, vagueness as a first-class non-error outcome, and
  the belief-default-position causing visible oscillating Thief movement),
  the full sanity-check-progression results table (§4: random policy →
  heuristic/Q-learning → the real LLM run's 75/45 Cop/Thief reversal), the
  learning curve (§5), and answers to 3 of the 4 required questions in
  full plus the 4th (cloud security trade-offs) answered for what's
  implemented (token auth + no-restart revocation) while explicitly
  flagging the broader cloud-security picture as pending Phase 5
  confirmation rather than overstating it. Two things in the report are
  deliberately left as open slots rather than faked: a real GUI screenshot
  (§6, needs a live run with a display — this session has none) and cloud
  reachability logs (§7, blocked on Phase 5). `README.md` rewritten from
  its Phase-0 placeholder into a full external-reader doc: install steps,
  local-run usage, cloud-run usage (with an explicit pending-confirmation
  note, not a claim that it's live), offline Q-learning training, a
  config-guide table, a tests section, and contribution guidelines.
  Deliberately did **not** touch `docs/ARCHITECTURE.md`'s URL placeholders
  or fill in `config.yaml: group.*` — those are Phase 5 tasks the user is
  already handling, and doing them here risked stepping on work in
  progress elsewhere.
- 2026-06-25: Phase 6 finished, now that Phase 5 closed out in parallel
  (both MCP servers confirmed reachable on Render, Gmail OAuth send
  confirmed — see Phase 5 above). Updated `reports/technical_report.md`
  §7 from a "pending" placeholder to real cloud-deployment evidence: both
  Render URLs, the `check_cloud_reachability.py` confirmation, and a full
  cloud-driven 6-sub-game series (Cop 90/Thief 40 — a different run from
  the local-mode 75/45 in §4, same regime, not expected to match exactly).
  §8's fourth required question (cloud security trade-offs) rewritten to
  cite that real evidence instead of hedging on missing confirmation —
  added the TLS-termination trade-off (Render handles it, not custom code
  in this project) and confirmed the OAuth secret/token files are
  gitignored and untracked. GUI screenshot (§6) now embedded too —
  `figures/gui_screenshot.png`, captured by the user from the leftover
  `results/live_state.json` final snapshot (move 9, 5×5 grid, capture
  moment at `(0,4)`, one barrier placed, both beliefs "high confidence")
  rather than re-running the whole series, since the GUI just polls
  whatever's already on disk. All four Phase 6 checklist items above are
  now `[x]` — Phase 6 is fully done.
- 2026-06-25: Strategy hardening, prompted by evaluating whether the
  current strategies are competitive enough for the (still-deferred)
  Phase 7 inter-group bonus. Three sequential fixes, each backed up
  separately (git tags `pre-strategy-rework` → `post-thief-fix` →
  `post-cop-fix` → this commit):
  1. **Thief belief-fallback exploit fix.** The Thief's "maximize distance
     from believed opponent" heuristic defaulted an unknown opponent
     position to the fixed grid center, which made it oscillate between
     the same one or two corner cells whenever belief confidence was
     "none" — a predictable pattern an opponent could learn to exploit.
  2. **Cop belief plausibility check.** `update_belief` now flags an
     NL-parsed position claim as implausible (downgrades confidence to
     "low" rather than discarding it) when it implies the opponent moved
     farther than physically possible (more than 1 cell per turn,
     8-directional movement) since the last estimate — so a Cop can't be
     made falsely "confident" by an internally-inconsistent bluff.
  3. **Q-learning retrained under partial observability** (the big one).
     Discovered while building fix #1's replacement that the random-
     coordinate fallback, while fine for the heuristic, was the wrong
     shape for a tabular Q-learner (no generalization across a different
     random coordinate every turn) — redesigned the "no estimate"
     representation as a shared, reserved sentinel (`UNKNOWN_POSITION =
     (-1, -1)` in `src/engine/board.py`, not `src/agents`, to respect the
     strategy-module dependency rule in `docs/PROMPTS.md`) that both the
     heuristic and Q-learning collapse to one bucket. Retrained both
     Q-tables against this sentinel + a real visibility-radius check
     during training (`scripts/train_q_learning.py`, default mode now
     partial-observability, `--full-visibility` flag preserves the old
     mode for comparison) — see `docs/prd/strategy.md`'s updated
     calibration record and `reports/technical_report.md` §5/§8 for the
     real result: the retrained Cop win-rate does **not** converge (noisy
     0.23–0.69, ends at 0.38), unlike the clean 1.0 convergence under full
     visibility — a genuine finding (tabular Q-learning's single shared
     "unknown" bucket can't represent a turn-varying correct answer), not
     a tuning failure. 108 tests passing project-wide (90% coverage),
     `belief.py` now 100%. The Thief fallback fix (#1) was itself revised
     mid-sequence to use the sentinel instead of a random coordinate, once
     this generalization problem surfaced — documented in commit history,
     not hidden.
- 2026-06-25: §20.9-checklist file-size compliance pass, requested
  explicitly before the next real run. Two files were over the 150-line
  limit: `src/strategy/q_learning.py` (175 lines) and
  `scripts/train_q_learning.py` (155 lines). Split rather than trimmed:
  `q_learning.py` → `q_learning_state.py` (state/action/reward helpers) +
  `q_learning_agent.py` (`QLearningAgent`) + `q_learning_training.py` (the
  training loop, now a `src/strategy/` library module instead of living
  directly in the script), all re-exported from the original
  `q_learning.py` path so no other file's imports needed to change.
  `scripts/train_q_learning.py` is now a thin CLI wrapper around
  `q_learning_training.train`. Added `tests/strategy/
  test_q_learning_training.py` (4 new tests) since the training loop
  moving into `src/` made it count toward coverage for the first time
  (previously invisible to `--cov=src` as a script). Max file length
  after the split: 136 lines (`src/agents/belief.py`). 111 tests
  project-wide, 91% coverage.
- 2026-06-25: First real cloud run with the strategy-hardening fixes
  active, against the same deployed Render servers, real Anthropic API
  calls (`run_llm_demo.py`, `algorithm: heuristic`). **Totals: Cop 105,
  Thief 35** (5 Cop captures, 1 Thief survival), no technical losses. The
  Thief fallback fix confirmed working on real output, not just under
  test: `results/transcripts/subgame_5x5_06_thief.txt` (the 50-turn
  survival sub-game) shows the Thief moving in 8 different directions
  while at "no reliable information" confidence almost the whole game —
  not the old fixed one-or-two-cell oscillation. The Cop plausibility
  check was present but never triggered (no "implausible" flag in any of
  the 6 transcripts) — a safety net for a failure mode that didn't happen
  to occur this run, not evidence it's inert.
  **Found and fixed a real problem from this run:** the email sent had
  every `sub_games` entry carrying the full per-turn transcript, several
  tens of thousands of characters total. Read the actual spec PDF
  directly (`ex06-Dual AI agent race via MCP servers.pdf`, §9.1) at the
  user's pointer — confirmed the official example shows `"sub_games": []`
  with no per-entry field schema, and the only stated content rule is
  "JSON body only, no free text"; §9's own stated purpose (automatic
  grading-system intake) argues for compact summary fields, not full NL
  transcripts, which remain required evidence elsewhere (§11,
  `results/transcripts/*.txt`, linked from the README) rather than
  embedded in the auto-graded email. `build_internal_game_json` now trims
  each `sub_games` entry via `_summarize_sub_game` (winner, moves_taken,
  final positions, barriers_placed, points only). Verified by rebuilding
  the report from this run's already-saved `results/*.json` files (no
  need to re-run the expensive cloud series) and sending a second real
  email: body length dropped from tens of thousands of characters to
  1,880. `docs/PLAN.md` ADR-7 and `docs/prd/email-reporting.md` record the
  decision and its honest caveat (the spec doesn't explicitly forbid a
  fuller entry either — this is the project's best read, not a literal
  quote, and `_SUB_GAME_SUMMARY_FIELDS` is the one place to revert if
  grading feedback says otherwise).
- 2026-06-25: **README.md spec-compliance correction.** Re-read
  `ex06-Dual AI agent race via MCP servers.pdf` §11 directly: it requires
  the scientific writeup — Dec-POMDP formal model, orchestration-challenge
  analysis, and visualization/evidence (learning curves, GUI screenshots,
  CLI logs proving cloud MCP communication) — to live *in README.md
  itself*, not in a separately-linked report file. The previous README
  only linked to `reports/technical_report.md` for all of that, which
  doesn't satisfy §11 literally. Rewrote `README.md` to embed all three
  required sections directly (Dec-POMDP tuple mapped to this project's
  code, the three orchestration-challenge findings with transcript
  evidence, and a new "Visualizations and evidence" section with both
  figures embedded inline plus a real CLI log excerpt from the
  2026-06-25 cloud run proving live communication against the deployed
  Render servers) while keeping the practical install/usage/config
  sections that were already there. `reports/technical_report.md` is kept
  as the *extended* writeup (full grid-size progression, all four
  required questions, qualitative transcript review) and is now described
  as supplementary in the README, not as the only place this content
  exists. All 111 tests still passing (docs-only change).
- 2026-06-25: Phase 7 bonus **code scaffolding** added, per explicit user
  request, while clarifying the coordination model first (the user's own
  proposed model — one side runs the live series, both sides email the
  same shared result — is correct, and is in fact the *only* workable
  one, since real LLM calls make two independent live runs of the same
  matchup non-reproducible). Nothing in Phases 0-6 was touched. New:
  `src/reporting/bonus_schema.py` (validates the §11.2 Inter-Group Bonus
  Game JSON shape — `report_type`, `groups`, both repos/URLs, both
  students lists, `totals_by_group`/`bonus_claim` keyed by team name with
  keys checked against `groups`' values, `mutual_agreement`),
  `bonus_report.py` (`build_bonus_game_json` merges two swapped-role
  `run_series_via_mcp` halves into one payload, correctly rolling each
  half's cop/thief points up to *team* names rather than roles, since the
  cop/thief-to-team mapping flips between halves; reuses
  `game_report.summarize_sub_game`, promoted from a private helper since
  it's now shared across two reporting modules — same compact-sub_games
  reasoning as ADR-7, both modules trim transcripts the same way),
  `bonus_scoring.py` (`compute_bonus_claim`: win=10/lose=7/tie=5;
  `average_bonus_score`: mean across valid series for multi-partner
  play). `scripts/run_bonus_series.py` is the CLI entrypoint — runs both
  halves via the existing `run_series_via_mcp` (no new orchestration
  logic needed, confirming the architecture already generalizes to this),
  builds/validates the payload, prints it for sharing with the partner
  group, and only emails our own copy if both `--send` and a new
  `config.yaml: bonus.send_on_completion` safety gate are set — mirrors
  the existing `reporting.send_on_completion` pattern, kept as a
  *separate* gate since the bonus email is independent of the mandatory
  one. `config.yaml` gained a `bonus.sub_games_per_half: 3` section
  (structural, not a secret — partner URLs/tokens are deliberately CLI
  arguments instead, never written to config or committed, since no
  partner exists yet and they're per-competition data). `gmail_sender
  .send_report` gained an optional `subject` parameter (default unchanged)
  so the bonus email is distinguishable from the mandatory one in an
  inbox. 15 new tests (`tests/reporting/test_bonus_{schema,report,
  scoring}.py`), 126 tests project-wide, 91% coverage, every file still
  ≤150 lines (`run_bonus_series.py` is the largest new file at 139).
  **Still blocked on an actual partner group** — `docs/prd
  /bonus-inter-group.md` and `docs/TODO.md`'s Phase 7 checklist both stay
  marked deferred; this is scaffolding, not a claim the bonus was
  attempted.
- 2026-06-25: Added exact-tie retry handling to the bonus scaffolding, per
  explicit user request (a 5/5 tie is lose-lose for both groups, so it's
  worth re-attempting rather than reporting). `src/reporting
  /bonus_scoring.py` gained `is_draw(totals_by_group)`. Extracted
  `_run_one_attempt`'s logic out of `scripts/run_bonus_series.py` into a
  new `src/agents/bonus_runner.py` (`run_one_bonus_attempt`) — needed
  because adding the retry loop pushed the script to 172 lines, over the
  150-line limit; this also made the run-one-attempt logic unit-testable
  on its own (`tests/agents/test_bonus_runner.py`, mocking
  `run_series_via_mcp` so no real network/LLM calls happen in the test).
  `scripts/run_bonus_series.py` now loops up to
  `config.yaml: bonus.max_draw_retries` (default 3) calling that
  function fresh each time, stopping early on any non-tie result. Two new
  config flags: `bonus.max_draw_retries` and
  `bonus.send_email_on_draw_after_max_retries` (default `false` — the
  safer "don't send a tied result" choice; per the user, this should be
  agreed with the partner group and set explicitly before a real run,
  not left at the default). 130 tests project-wide, 92% coverage, every
  file still ≤150 lines (`run_bonus_series.py` 129,
  `bonus_runner.py` 68).
- 2026-06-25: Closed a real gap the user caught — "share the JSON, partner
  pastes it into an email by hand" does **not** satisfy the lecturer's
  "each group sends automatically from the code" requirement on the
  partner's side. Added `scripts/send_bonus_report.py`: the partner
  group's entrypoint — loads the shared payload file, validates it
  against `bonus_schema`, **refuses to send unless `mutual_agreement` is
  already `true`** (manually verified: passing a `mutual_agreement:
  false` payload raises and exits 1, doesn't silently send), and sends
  via the caller's *own* Gmail OAuth (`GMAIL_CLIENT_SECRET_PATH`/
  `GMAIL_TOKEN_PATH` already required for their own mandatory
  submission — nothing from our `.env`, and nothing of theirs needed
  beyond that). No game-playing, no MCP/LLM calls in this script at all —
  purely "load, validate, send." Also clarified in
  `docs/prd/bonus-inter-group.md` (new "Trust boundary, explicitly
  minimal" note) exactly what the partner group does and doesn't need to
  share: two revocable MCP bearer tokens, nothing else — never their LLM
  key, never their Gmail credentials. No test added for this script,
  matching the existing convention that thin CLI wrappers around already-
  tested `src/` functions (`run_llm_demo.py`, `train_q_learning.py`, etc.)
  don't get their own test file.
- 2026-06-25: **Phase 8 (final QA gate) done** for everything codeable.
  Full suite re-run clean (133 tests, 92% coverage). Verified: no file
  over 150 lines (largest `scripts/run_bonus_series.py` at 142), every
  `src/` module has a docstring (checked by script, zero misses), no
  secrets ever entered git history (`git log --all --full-history` on
  `.env`/`secrets/`/token/client-secret paths returns empty; `git grep`
  for Anthropic/Google API-key-shaped strings across tracked files found
  nothing). Found and fixed one real gap: §20.9 asks for a token-usage
  table with cost analysis, which didn't exist anywhere — added
  `reports/technical_report.md` §9, grounded in the real saved
  transcripts (258 logged `Message:` lines, avg 75.6 chars) and the
  configured `max_tokens` ceilings rather than fabricated precision,
  since this project never instrumented per-call `usage` tracking;
  flagged that gap explicitly in the report itself as a concrete future
  extension point rather than papering over it. Also fixed `LICENSE`,
  which still had a placeholder `Copyright (c) 2026 Team` — replaced with
  the real names from `config.yaml: group.students`. Updated stale test
  counts in README (111/91% → 133/92%). **Two Phase 8 items remain
  genuinely not codeable, left for the user**: confirming the exact
  submission deadline/time, and the actual submission through the
  course's submission space — both require information/access this
  session doesn't have.
- 2026-06-25: **Real architectural correction to the bonus design**,
  caught by the user before anything was sent to a partner group: the
  previous design had one side's orchestrator decide *both* agents' moves
  each half, submitting to whichever server owned that role. That ran
  fine, but it never actually exercised the partner group's own
  strategy/LLM at all — their server was just a passive validator,
  defeating the entire point of an inter-group competition. Redesigned
  from scratch (`docs/PLAN.md` ADR-8, `docs/prd/bonus-inter-group.md`'s
  new "Architecture" section): **both groups now run
  `scripts/run_bonus_series.py` simultaneously**, each deciding only its
  own agent's moves with its own strategy/LLM. New modules, split for the
  150-line limit (one logical unit): `src/agents/bonus_peer.py` (low-level
  helpers — `client`, `wait_for_opponent_move` polling-based turn-sync,
  `positions` via `report_location` on both servers, `act` — decide +
  submit one turn), `bonus_peer_subgame.py` (one sub-game's turn loop,
  capture-checked after every move from each side's own observation),
  `bonus_peer_half.py` (loops `sub_games_per_half`, derives shared
  starting positions from `str((series_seed, half_index, sub_game_index))`
  so both sides agree without coordinating over the network — `random
  .Random` doesn't accept tuple seeds directly, caught by a failing test).
  `src/engine/start_positions.py:random_start_positions` gained an
  optional `rng` param for this. `src/agents/orchestrator_series.py`'s
  `_score_subgame` promoted to public `score_subgame` (now reused
  cross-module) and its `from src.agents import orchestrator` moved to a
  lazy import inside the one function that needs it — fixed a real
  circular-import crash (`orchestrator.py` re-exports from
  `orchestrator_series.py` at its own bottom; importing
  `orchestrator_series` directly, as the new bonus modules do, hit the
  cycle in the wrong order). `bonus_runner.run_one_bonus_attempt` now
  calls `run_bonus_half_as_peer` per half instead of `run_series_via_mcp`,
  gained a required `series_seed` param; `scripts/run_bonus_series.py`
  gained `--series-seed` (required) and documents that **both** sides run
  it, with matching `--our-role-half1`/`--series-seed`/
  `bonus.max_draw_retries`. Rewrote `tests/agents/test_bonus_runner.py`
  to mock the new boundary. New `tests/agents/test_bonus_peer.py` — the
  key evidence: runs both sides of a sub-game/half **concurrently**
  (`asyncio.gather`) against two real in-process MCP servers (no network),
  asserting they independently agree on the winner/totals without either
  one telling the other anything; a first draft of this test only drove
  one side and hung forever waiting for a move nobody was submitting —
  the exact bug this whole redesign exists to fix, caught immediately by
  the test itself. 133 tests project-wide, 92% coverage, every file still
  ≤150 lines (`run_bonus_series.py` 142, the largest).
