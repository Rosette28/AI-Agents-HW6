# PRD — Cop & Thief: MCP-Based Multi-Agent Pursuit Game

## Project overview and context

This project is HW06 (L09) for the AI Agents course: build an end-to-end
pipeline in which two autonomous AI agents — a **Cop** and a **Thief** —
play a pursuit game on a 2D grid. Each agent is driven by an LLM-based
orchestrator (Client) and communicates with the other exclusively through
**free natural language**, routed through two independent **MCP servers**
(one per agent). The value being assessed is not who wins, but whether the
**orchestration** — NL parsing, belief inference under partial observation,
and translation of inferred beliefs into board actions — works end to end,
autonomously, across a full 6-sub-game series, with results self-reported by
email.

## User problem / central claim

There is no existing reference implementation the course provides; the
"problem" is proving a specific claim:

> Two independent AI agents, each behind its own MCP server, can communicate
> only in free natural language (no rigid coordinate protocol) and
> autonomously play a complete 6-round pursuit game, inferring each other's
> position from partial observations and self-reporting the final result.

Everything in this PRD serves that claim.

## Audience

- **Primary grader:** the course instructor/TA, evaluating against the
  course's "AI-agent software submission" rubric and the §20.9 QA checklist
  (modular architecture, docs, tests, security, visualization, cost
  tracking).
- **Secondary:** an optional partner group, for the inter-group bonus game
  (Phase 7), who will integrate against this project's two public MCP URLs.

## Goals, KPIs, and acceptance criteria

| Goal | Acceptance criterion |
|---|---|
| Full pipeline runs end to end | A complete 6-sub-game series executes locally without manual intervention |
| Agents use only free NL | No numeric coordinates appear in the inter-agent message payloads (verified by transcript review) |
| Partial observability is real | Agents only resolve opponent position within `observation.visibility_radius`; transcripts show reasoning under uncertainty |
| Cloud deployment works | Both MCP servers reachable over HTTPS with token auth (+ revocation demonstrated) |
| Scoring is correct | Totals from a recorded run match the scoring table in `config.yaml` exactly |
| Automatic reporting works | One summary email is sent automatically after sub-game 6, body = Internal Game JSON only |
| Documentation complete | PRD, PLAN, TODO, CONCEPTS, API, PROMPTS, README all present and consistent with the §20.9 checklist |
| Test coverage | ≥85% coverage across `src/` |
| Generic board size | Grid size changes via `config.yaml` only — no hardcoded 5×5 assumptions in code |

## Functional requirements

- FR1: Board state machine supporting configurable grid size, 8-directional
  movement, and barrier placement (Cop only, capped at `max_barriers`).
- FR2: Win-condition detection — capture (exact cell match) or survival
  (Thief outlasts `max_moves`).
- FR3: Two independent MCP servers (Cop, Thief) exposing tools: read
  message, report/verify own location (internal, scoring-only), send NL
  message, choose & execute an action.
- FR4: LLM-based orchestrator per agent that parses incoming NL messages,
  updates an internal belief about the opponent's position, and decides the
  next action (via heuristic and/or Q-learning strategy module).
- FR5: Sub-game loop (≤25 moves) and full-series loop (6 sub-games) with
  per-sub-game and cumulative scoring.
- FR6: GUI showing grid, agent positions, barriers, updating in real time.
- FR7: Automatic email reporting (Internal Game JSON only) after the 6th
  sub-game, with technical-loss detection and re-run.
- FR8: Token-based auth with revocation support on both MCP servers.

## Non-functional requirements

- NFR1: Modular codebase, files ≤150 lines, docstrings, consistent style.
- NFR2: No hardcoded parameters — everything tunable lives in
  `config/config.yaml`.
- NFR3: No secrets committed; all credentials via `.env` (gitignored).
- NFR4: MCP servers reachable from the public internet over HTTPS, not
  testable from a network that blocks non-standard ports.
- NFR5: ≥85% automated test coverage.
- NFR6: Reproducible environment via pinned dependencies.

## User stories

- As the **Cop agent**, I want to interpret the Thief's NL hints (truthful
  or bluffed) so that I can update my belief about its location and decide
  whether to move toward it or place a barrier.
- As the **Thief agent**, I want to describe my situation ambiguously or
  misleadingly in NL so that I can evade capture without revealing my exact
  position.
- As the **grader**, I want a single email with a clean JSON payload so that
  I can automatically ingest the result of a group's full 6-sub-game series.
- As a **developer on this team**, I want the grid size to be a config
  value so that I can sanity-check the pipeline on a 1×2 board before
  scaling to 5×5.

## Assumptions, dependencies, constraints, out-of-scope

**Assumptions**
- Approach 1 (cloud LLM API) is used for the LLM deployment (see ADR in
  `docs/PLAN.md`).
- A single team builds and owns the Cop and Thief implementations; the
  bonus inter-group game is a stretch goal, not required for the base grade.

**Dependencies**
- `fastmcp` for MCP servers, a cloud LLM SDK (Anthropic, paid tier), Gmail API
  (`google-api-python-client`) for reporting, `pyyaml` for config, `pandas`/
  `matplotlib` for analysis graphs, `pytest` for tests.

**Constraints**
- Max 25 moves per sub-game, max 5 barriers per sub-game, exactly 6
  sub-games per series — all enforced via config, not hardcoded numbers in
  game logic.
- Agents must never exchange numeric coordinates directly — enforced by
  design (the wire format between agents is NL text only) and spot-checked
  in transcript review.

**Out of scope (for the mandatory submission)**
- Deep neural network training (Tabular Q-learning is the recommended
  ceiling, not deep RL).
- The inter-group bonus competition is Phase 7 — separate, optional, scored
  independently.

## Timeline and milestones

Mirrors the phase breakdown in `docs/TODO.md` / `hw06_project_plan.md`:

| Phase | Deliverable |
|---|---|
| 0 | Planning docs, repo skeleton, env setup |
| 1 | Game engine verified locally, no agents |
| 2 | MCP servers + orchestrators wired, full local run |
| 3 | Strategy module (heuristic / Q-learning) |
| 4 | Free NL dialogue + GUI + learning curves |
| 5 | Cloud deployment, security, automated Gmail reporting |
| 6 | Dec-POMDP write-up, README, technical report |
| 7 (bonus) | Inter-group cloud competition |
| 8 | Final QA against §20.9 checklist, submission |
