# Cop & Thief: MCP-Based Multi-Agent Pursuit Game

Two independent AI agents — a **Cop** and a **Thief** — communicate
exclusively through **free natural language** over two separate MCP
servers, each with no visibility into the other's exact state, and play a
complete 6-round pursuit game end to end, with results self-reported by
email.

See `docs/PRD.md` for the full goal and success criteria, `docs/PLAN.md`
for architecture (C4 diagrams, ADRs), `docs/TODO.md` for live progress, and
`reports/technical_report.md` for the full write-up (Dec-POMDP model,
orchestration-challenge analysis, results, learning curves).

## Repository layout

See `docs/PLAN.md` for the annotated structure. In short:

- `src/` — engine, MCP servers, agent orchestrators, strategy, GUI, reporting
- `config/config.yaml` — every tunable parameter (grid size, scoring, etc.)
- `docs/` — planning and design docs (PRD, PLAN, TODO, CONCEPTS, API, PROMPTS)
- `tests/` — unit tests (target ≥85% coverage; currently 89%)
- `scripts/` — entrypoints (run servers, run the LLM demo, train Q-learning,
  plot the learning curve, check cloud reachability)
- `results/`, `figures/`, `reports/` — run outputs, generated graphs, the
  technical writeup

## Installation

```bash
uv venv
uv pip install -r requirements.txt
```

(or `python -m venv .venv && pip install -r requirements.txt` if not using
`uv`).

Copy `.env.example` to `.env` and fill in:

- `ANTHROPIC_API_KEY` — required for any real LLM-driven run.
- `COP_MCP_AUTH_TOKEN` / `THIEF_MCP_AUTH_TOKEN` — bearer tokens for the two
  MCP servers (generate your own; never commit real values).
- `COP_MCP_URL` / `THIEF_MCP_URL` — only needed once you're pointing the
  demo at cloud-deployed servers rather than running them locally.
- `GMAIL_CLIENT_SECRET_PATH` / `GMAIL_TOKEN_PATH` — only needed for
  automated email reporting; the demo skips reporting with a clear message
  if these are unset.

Review `config/config.yaml` — see **Configuration guide** below.

## Usage

### Local run (no cloud deployment needed)

```bash
# Terminal 1 — both MCP servers in one process, for local dev
python scripts/run_mcp_servers.py

# Terminal 2 — drives a full 6-sub-game series through the MCP chain
python scripts/run_llm_demo.py
```

`run_llm_demo.py` runs the full series, writes a transcript per sub-game to
`results/transcripts/`, writes the live GUI state snapshot, and (if Gmail
credentials are set) sends the Internal Game JSON report automatically
after the 6th sub-game.

To watch the live board while a series runs:

```bash
streamlit run src/gui/app.py
```

### Cloud run

Each MCP server can run standalone (one per process/host) via:

```bash
MCP_SERVER_ROLE=cop   PORT=8001 python scripts/run_mcp_servers.py
MCP_SERVER_ROLE=thief PORT=8002 python scripts/run_mcp_servers.py
```

Point your hosting platform at this entrypoint per server. Once both are
deployed, set `COP_MCP_URL`/`THIEF_MCP_URL` in `.env` and verify reachability:

```bash
python scripts/check_cloud_reachability.py
```

> **Status:** `config/config.yaml` already has Render URLs configured for
> both servers; public-HTTPS reachability and the Gmail OAuth send are
> being finished outside this report (Phase 5) — see `docs/TODO.md` for the
> exact remaining checklist. Nothing above the cloud-run/reporting steps
> requires that to be finished first.

### Offline Q-learning training (optional strategy)

```bash
python scripts/train_q_learning.py
python scripts/plot_learning_curve.py   # renders figures/learning_curve.png
```

### Bonus inter-group run

Not currently pursued (deferred per `docs/TODO.md` Phase 7); would reuse
the same cloud-run setup against a partner group's independently-deployed
MCP server URLs.

## Configuration guide

Everything tunable lives in `config/config.yaml` — nothing in `src/` should
hardcode a value that belongs here:

| Section | Key parameters |
|---|---|
| `board` | `grid_size`, `max_barriers` |
| `game` | `max_moves` (per sub-game), `num_games` (sub-games per series) |
| `scoring` | per-outcome point values (capture / survival, both sides) |
| `observation` | `visibility_radius` — partial-observability range |
| `llm` | `provider`, `model` — which LLM the orchestrators call |
| `strategy` | `algorithm` (`heuristic` or `q_learning`), plus
  `q_learning.{alpha,gamma,epsilon,epsilon_decay,epsilon_floor}` |
| `mcp` | `cop_mcp_url`, `thief_mcp_url`, ports for local dev |
| `reporting` | `recipient_email` |
| `group` | `group_name`, `students`, `github_repo` — fill in before a real
  Gmail send; the report payload includes this |

## Tests

```bash
pytest --cov=src --cov-report=term-missing
```

99 tests, 89% project-wide coverage at last check (target ≥85%).

## Contributing

This is a course assignment with a single-team scope (see `docs/PRD.md`'s
assumptions). If extending it: keep the Client/Server split strict (no LLM
import under `src/mcp_servers/`), keep strategy code belief-agnostic (it
should only ever consume a `Board`, never an MCP session directly), and
add a test alongside any new module before treating it as done — see
`docs/TODO.md`'s phase breakdown for the pattern this project followed.

## License

MIT — see `LICENSE`.
