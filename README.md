# Cop & Thief: MCP-Based Multi-Agent Pursuit Game

> Status: Phase 0 (planning) in progress. This README is a placeholder — the full
> scientific writeup (Dec-POMDP formalization, orchestration analysis, results,
> graphs, GUI screenshots, cloud logs) will be assembled in Phase 6.

## What this project proves

Two independent AI agents — a **Cop** and a **Thief** — communicate exclusively
through **free natural language** over two separate MCP servers, each with no
visibility into the other's exact state, and play a complete 6-round pursuit
game end to end, with results self-reported by email.

See `docs/PRD.md` for the full goal and success criteria, `docs/PLAN.md` for
architecture, and `docs/TODO.md` for current progress.

## Repository layout

See `docs/PLAN.md` for the annotated structure. In short:

- `src/` — engine, MCP servers, agent orchestrators, strategy, GUI, reporting
- `config/config.yaml` — every tunable parameter (grid size, scoring, etc.)
- `docs/` — planning and design docs (PRD, PLAN, TODO, CONCEPTS, API, PROMPTS)
- `tests/` — unit tests (target ≥85% coverage)
- `results/`, `figures/`, `reports/` — run outputs, generated graphs, the
  technical writeup

## Setup

Instructions will be filled in once the environment and dependencies are
finalized (Phase 0). Outline:

1. `uv venv && uv pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your LLM API key + Gmail OAuth
   credential paths.
3. Review `config/config.yaml` and adjust parameters if needed.

## License

MIT — see `LICENSE`.
