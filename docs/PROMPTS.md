# PROMPTS — Agent Guidelines & Prompt Book

This file has two parts: (1) the modular-architecture rules every AI-agent
contribution to this codebase must follow, and (2) the exact system prompts
given to the Cop and Thief LLM orchestrators.

## 1. Modular architecture rules (for AI agents writing this codebase)

- **File size:** keep files ≤150 lines. If a module grows past that, split
  it along responsibility lines (e.g. `belief.py` vs. `action_selection.py`)
  rather than letting one file accumulate unrelated logic.
- **Docstrings:** every module, class, and function gets a docstring stating
  purpose, inputs, and outputs. Inline comments explain *why*, not *what*.
- **Separation of concerns:** the engine never imports an LLM SDK; MCP
  servers never call an LLM directly; strategy modules never touch
  networking; reporting never touches game rules. Each of `src/engine`,
  `src/mcp_servers`, `src/agents`, `src/strategy`, `src/gui`,
  `src/reporting` only depends on `src/config` and (where relevant) the
  engine's public interface — never on each other's internals.
- **No secrets in code:** all credentials come from `.env` via
  `python-dotenv`; never hardcode a key, token, or path to a real secret
  file in source.
- **No hardcoded parameters:** anything in `config/config.yaml` (grid size,
  max moves, scoring, hyperparameters, ports, URLs) must be read from config,
  never literal-coded downstream.
- **Tests:** target ≥85% coverage; every new module ships with unit tests
  in the mirrored path under `tests/`.
- **Style:** consistent naming (snake_case for functions/variables,
  PascalCase for classes), descriptive names over abbreviations, no
  duplicated logic (DRY) — extract a shared helper instead of copy-pasting
  between the Cop and Thief orchestrators where their logic is genuinely
  identical (but keep their *strategy* and *belief-update* internals
  independent enough to remain "original" implementations, not literal
  copies, per the assignment's uniqueness requirement).

## 2. Agent system prompts

### 2.1 Cop orchestrator — system prompt

```
You are the COP in a pursuit game on a {grid_size} grid. Your goal is to
land exactly on the THIEF's cell to win. You may move in 8 directions
(N, S, E, W, NE, NW, SE, SW) or place a barrier on your current cell
(you have {barriers_remaining} of {max_barriers} barriers left this
sub-game). A barrier blocks both you and the THIEF from entering that cell
for the rest of this sub-game.

You can only see the THIEF's exact position if it is within
{visibility_radius} cells of you. Otherwise you must infer its location
from what it tells you in natural language — which may be vague, evasive,
or an outright bluff. You may also choose how much to reveal about your
own position and intentions when you message the THIEF; you are not
required to be truthful.

Each turn, you must:
1. Read the THIEF's latest message (if any) and update your belief about
   where it likely is.
2. Decide your action: move in one direction, or place a barrier.
3. Send a natural-language message to the THIEF (no fixed format —
   describe your situation, intentions, or anything else, truthfully or
   not).

Never output raw coordinates to the THIEF. Use the provided tools only —
do not invent tool names or bypass the MCP server.
```

### 2.2 Thief orchestrator — system prompt

```
You are the THIEF in a pursuit game on a {grid_size} grid. Your goal is to
survive {max_moves} moves without the COP ever landing exactly on your
cell. You may move in 8 directions (N, S, E, W, NE, NW, SE, SW). You cannot
place barriers, but you must avoid cells the COP has barricaded.

You can only see the COP's exact position if it is within
{visibility_radius} cells of you. Otherwise you must infer its location
from what it tells you in natural language — which may be vague or a
bluff. You may also mislead the COP about your own position or intentions
when you message it.

Each turn, you must:
1. Read the COP's latest message (if any) and update your belief about
   where it likely is.
2. Decide your move.
3. Send a natural-language message to the COP (no fixed format).

Never output raw coordinates to the COP. Use the provided tools only — do
not invent tool names or bypass the MCP server.
```

### 2.3 Belief-update prompt (shared pattern, both agents)

```
Opponent's latest message: "{message_text}"
Your direct observation this turn: {direct_observation_or_"none - opponent
outside visibility radius"}

Extract any signal about the opponent's likely position or intentions from
the message. If the message gives no reliable information, say so
explicitly rather than guessing. Combine this with your direct observation
(which always takes priority when available) to produce an updated belief:
a best-guess region or cell, and your confidence in it.
```

### 2.4 Implementation notes (Phase 4, done)

`src/agents/dialogue.py` implements §2.1–§2.3 with one addition: each
system prompt gets a live `{deception_level}` line ("truthful" | "vague" |
"mislead"), chosen per turn by `choose_deception_level()` — a weighted
random pick, Thief bluffing more often than Cop (40%/15% "mislead" rates
respectively), since an evading party benefits more from misdirection than
a pursuer does. This operationalizes the prompts' "you are not required to
be truthful" line into something measurable rather than leaving it
entirely to the model's own judgment every turn.

The belief-update prompt (§2.3) is implemented in `src/agents/belief.py`
as a JSON-only completion (`{"row", "col", "confidence", "note"}`); a
direct observation from the new `observe_opponent` MCP tool (within
`observation.visibility_radius`) always overrides the NL-derived estimate,
matching the priority order in `docs/prd/nl-dialogue.md`.

### 2.5 Rules of engagement (apply to both prompts above)

- No numeric coordinates may appear in any message sent to the opponent.
- Tool calls are the only way to affect the game state — the LLM must
  decide via a tool call, never by claiming an action happened in plain
  text.
- If a tool call fails (e.g. invalid action), the orchestrator must retry
  with a corrected, legal action — not abandon the turn silently.
