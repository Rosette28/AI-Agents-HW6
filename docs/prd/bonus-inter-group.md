# Mini-PRD — Bonus Inter-Group Cloud Competition

## Description / theoretical background

Optional bonus (up to 10 points toward the final project): two groups each
deploy their own Cop + Thief MCP servers to the cloud and play a full
two-sided 6-sub-game series against each other — 3 sub-games with Group A's
Cop vs. Group B's Thief, then 3 with roles swapped. Code/architecture may be
shared between partner groups, but each group's agent implementation and
internal strategy must remain unique and original.

## Requirements, inputs/outputs

- **Input:** both groups' public MCP URLs (Cop + Thief each), agreed token
  auth so each group's Client can call into the other's server.
- **Output:** an Inter-Group Bonus Game JSON (§11.2 of the requirements),
  sent independently by both groups, with `mutual_agreement: true` and
  **identical** result fields.

## Algorithm / process

1. Confirm partner group, exchange the four MCP URLs + auth scheme.
2. Run 3 sub-games: Group A Cop vs. Group B Thief.
3. Run 3 sub-games: Group B Cop vs. Group A Thief.
4. Each group independently computes totals and cross-checks with the
   partner group before either side sends anything.
5. Both groups send separate emails with byte-for-byte matching result
   fields and `mutual_agreement: true`.

## Constraints and limitations, alternatives considered

- A result mismatch between the two groups' emails disqualifies both groups
  for that series (0 bonus points) — cross-checking before sending is not
  optional.
- Bonus scoring: win a series = 10 pts, lose = 7 pts, exact tie = 5 pts
  each; final bonus = average across all valid series if playing multiple
  partner groups.
- **Alternative considered:** sharing the entire codebase with the partner
  group — rejected; only the game engine/architecture may be shared, the
  agent implementation and strategy must stay unique per group (graded on
  originality).

## Edge cases

- Partner group's server goes down mid-series — treat as a technical loss
  for that sub-game per the same rules as the base game; re-run before
  finalizing the series result.
- Disagreement discovered only after one side already sent its email — do
  not send a corrected email without re-confirming agreement with the
  partner group first; document the discrepancy.

## Success criteria / test scenarios

- Full NL transcripts + logs proving 6 autonomous cross-group sub-games.
- Two emails (one per group) with matching JSON, captured as evidence.
- Bonus score computed and recorded in `docs/TODO.md`.
