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

- [ ] **Implement the board as a state machine with a configurable grid
  size**
  - Priority: High
  - Status: not started
  - Definition of done: grid size is read from `config.board.grid_size`;
    nothing in the engine assumes 5×5; the same code path handles a 1×2
    board and a 5×5 board identically.

- [ ] **8-directional movement with boundary validation**
  - Priority: High
  - Status: not started
  - Definition of done: all 8 directions (N, S, E, W, NE, NW, SE, SW) are
    supported; moves off the board are rejected with a clear reason, not a
    crash.

- [ ] **Turn order (Thief moves first, then Cop, repeating)**
  - Priority: High
  - Status: not started
  - Definition of done: the engine enforces strict alternation and exposes
    whose turn it is at any point in a sub-game.

- [ ] **Barrier placement (Cop only, capped at `max_barriers`)**
  - Priority: High
  - Status: not started
  - Definition of done: only the Cop can place a barrier; barriers block
    both agents from entering that cell for the rest of the sub-game; the
    Cop cannot exceed `max_barriers` placements in one sub-game; placing a
    barrier on the Cop's own current cell does not trap the Cop with zero
    legal moves (decide and implement a no-legal-moves fallback, e.g. skip
    turn).

- [ ] **Win conditions: capture and survival**
  - Priority: High
  - Status: not started
  - Definition of done: capture is detected the instant the Cop's position
    exactly matches the Thief's; survival is declared once the Thief
    completes `max_moves` without ever being captured.

- [ ] **Sub-game loop (≤25 moves) and full-game loop (6 sub-games)**
  - Priority: High
  - Status: not started
  - Definition of done: a sub-game terminates correctly on capture,
    survival, or the move cap; a full series runs exactly `num_games`
    sub-games back to back and accumulates per-sub-game scores into a
    series total matching the scoring table.

- [ ] **Persist every raw sub-game result to `results/*.json`**
  - Priority: Medium
  - Status: not started
  - Definition of done: each result file is tagged by scenario (grid size,
    sub-game index, winner) and is written automatically, never
    hand-edited afterward.

- [ ] **Sanity check on a 1×2 grid**
  - Priority: High
  - Status: not started
  - Definition of done: win conditions, barrier logic, and scoring all
    behave correctly on the smallest possible board, run before scaling up
    to anything larger — this is meant to catch off-by-one and edge-case
    bugs cheaply.

- [ ] **Unit tests: movement validation, barrier blocking, capture
  detection, survival detection, score accumulation**
  - Priority: High
  - Status: not started
  - Definition of done: each of these five behaviors has a dedicated,
    passing test, and the suite catches a deliberately-introduced
    regression in any one of them.

---

## Phase 2 — MCP Infrastructure & Full Local Run

- [ ] **Stand up two MCP servers (Cop, Thief) using FastMCP**
  - Priority: High
  - Status: not started
  - Definition of done: each server lives in its own module under
    `src/mcp_servers/`, runs on its own port, and is independently
    startable/stoppable.

- [ ] **Expose the required tools on each server**
  - Priority: High
  - Status: not started
  - Definition of done: read incoming message, report/verify own location
    (internal/scoring-only, never leaking the opponent's exact position),
    send a natural-language message, and choose-and-execute an action
    (move/barrier) are all implemented and match `docs/API.md`.

- [ ] **Document each tool's contract in `docs/API.md`**
  - Priority: High
  - Status: in progress — a first-draft contract exists; needs to be kept
    in sync with the actual implementation as it's built, not just left as
    the planning-stage version.
  - Definition of done: the doc accurately reflects the real request/
    response shape of every tool, including error formats.

- [ ] **Confirm Client/Server separation**
  - Priority: High
  - Status: not started
  - Definition of done: grep/inspect `src/mcp_servers/` and confirm it
    never imports or calls an LLM SDK directly — all LLM calls live in
    `src/agents/`.

- [ ] **Run both servers locally on separate ports, verify mutual
  reachability with a trivial ping/echo tool call**
  - Priority: High
  - Status: not started
  - Definition of done: a manual or scripted ping/echo round-trip succeeds
    between both servers before any real game logic is wired through them.

- [ ] **Pipeline sanity check on the 1×2 grid**
  - Priority: High
  - Status: not started
  - Definition of done: a dummy message travels end to end (Client → tool
    call → MCP server → response) on the smallest board, and is logged
    correctly.

- [ ] **Wire up the full chain: orchestrator → LLM → tool-call decision →
  MCP server → engine update → result back to orchestrator**
  - Priority: High
  - Status: not started
  - Definition of done: a single turn can be driven entirely through this
    chain without any manual intervention or hardcoded shortcut.

- [ ] **Run a complete sub-game between the two agents on localhost**
  - Priority: High
  - Status: not started
  - Definition of done: one full sub-game (ending in capture or survival)
    completes autonomously, with a readable transcript and log.

- [ ] **Run a full 6-sub-game series locally and confirm totals match
  Table 1's scoring rules**
  - Priority: High
  - Status: not started
  - Definition of done: the series-level total score exactly matches what
    you'd compute by hand from the per-sub-game outcomes and the scoring
    table in `config.yaml`.

- [ ] **Sanity progression: 1×2 → 2×3/3×2 → 3×4/4×3 → 5×5**
  - Priority: Medium
  - Status: not started
  - Definition of done: each grid size in the progression is run at least
    once, with observations about convergence issues, hyperparameter
    problems, and observation-radius effects recorded in the notes log at
    the bottom of this file.

---

## Phase 3 — Strategy / Decision-Making Mechanism

- [ ] **Implement a heuristic strategy (Manhattan distance / decision
  tree) in `src/strategy/`**
  - Priority: High
  - Status: not started
  - Definition of done: both Cop and Thief have a working heuristic that
    produces sensible moves (Cop closes distance, Thief opens it) and the
    pipeline runs without needing Q-learning yet.

- [ ] **Implement Tabular Q-Learning, if pursued**
  - Priority: Medium
  - Status: not started
  - Definition of done: State/Action/Reward are defined concretely, the
    Bellman update and epsilon-greedy exploration are implemented, episode
    bookkeeping works across sub-games, and the learned Q-table is
    persisted to `results/`.

- [ ] **Calibrate hyperparameters (α, γ, ε) and record the reasoning**
  - Priority: Medium
  - Status: not started
  - Definition of done: the chosen values and *why* they were chosen are
    written into `docs/prd/strategy.md`, not just left as the config
    defaults with no justification.

- [ ] **Confirm the Cop's and Thief's strategies are unique and original
  implementations**
  - Priority: Low
  - Status: not started
  - Definition of done: if any code is shared with a partner group (bonus
    scenario), the mini-PRD explicitly notes how this project's agent
    implementation and strategy differ from anything shared.

- [ ] **Unit tests for the Q-table update rule and the action-selection
  policy**
  - Priority: Medium
  - Status: not started
  - Definition of done: a known transition produces the exact expected
    Q-value update; epsilon-greedy action selection statistically respects
    the configured epsilon across many trials.

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
