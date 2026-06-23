# Mini-PRD — Natural-Language Dialogue

## Description / theoretical background

This is the heart of the assignment: the only channel between Cop and
Thief is free natural language, generated and interpreted by each agent's
LLM. There is no rigid schema — no coordinates, no fixed keywords required.
Each agent must produce messages consistent with its own strategy (which
may include deliberate vagueness or bluffing) and must parse the opponent's
messages into an updated belief, despite genuine linguistic ambiguity.

## Requirements, inputs/outputs

- **Input to message generation:** own belief state, own intended action,
  an optional "deception level" parameter the strategy may set (e.g. "reveal
  truthfully" vs. "mislead").
- **Output of message generation:** a free-text NL message sent via the
  `send_message` MCP tool.
- **Input to belief update:** the opponent's latest NL message + the
  agent's own partial observation (visibility-radius check).
- **Output of belief update:** a revised internal estimate of the
  opponent's likely position (point estimate, region, or confidence note),
  consumed by the strategy module.

## Algorithm

1. Generate message: prompt the LLM with the agent's role, current state,
   and instruction to communicate in free NL (system prompt defined in
   `docs/PROMPTS.md`).
2. Parse message: prompt the LLM with the opponent's raw text and ask it to
   extract any positional/intent signal, explicitly allowing "no reliable
   information" as a valid extraction outcome.
3. Merge with direct observation: if the opponent is within
   `visibility_radius`, the direct observation overrides/corrects whatever
   the NL message implied (this is also where bluffing becomes detectable
   over time).
4. Feed the merged belief into the strategy module for action selection.

## Constraints and limitations, alternatives considered

- No predefined protocol or fixed vocabulary may be enforced on the
  messages — this is a hard constraint of the assignment, not a simplifying
  option.
- **Alternative considered:** structured JSON messages with a "flavor text"
  field — rejected; it would defeat the purpose of testing genuine NL
  orchestration.

## Edge cases

- Opponent message is nonsensical, off-topic, or empty (LLM hallucination,
  API hiccup) — belief update must degrade gracefully to "no new
  information," not crash or freeze the turn loop.
- Self-contradictory message across turns (intentional bluffing or model
  inconsistency) — log it; do not attempt to silently "correct" the
  opponent's message.

## Success criteria / test scenarios

- Full NL transcripts for all 6 sub-games are logged to `results/`/`logs/`
  and are human-readable evidence of autonomous operation.
- At least one qualitative note in `docs/TODO.md` describing any ambiguous
  or nonsensical message encountered and how it was handled.
- No numeric coordinates appear in any logged inter-agent message (spot
  checked across transcripts).
