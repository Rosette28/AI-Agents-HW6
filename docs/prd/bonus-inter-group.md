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
- **Trust boundary, explicitly minimal:** the only thing the partner group
  needs to share is a bearer token for each of their two servers — ideally
  a fresh, single-purpose token they mint just for this competition and
  revoke afterward (`src.mcp_servers.auth.revoke_token`, already built and
  tested — takes effect on the very next request, no restart needed).
  Nothing else from their `.env` is ever needed: not their LLM API key
  (we never call their model, only their MCP tool endpoints), and not
  their Gmail credentials (each side sends from their own inbox using
  their own already-configured OAuth).

## Architecture: why BOTH groups must run their own process

**This was wrong in an earlier draft of this design, caught during review:**
the first implementation had one side's orchestrator decide *both* agents'
moves, submitting them to whichever server (ours or the partner's) happened
to own that role. That technically "worked," but it never actually
exercised the partner group's own strategy or LLM at all — their server
was reduced to a passive position/barrier validator. The whole point of an
inter-group competition is each side's *own* agent playing against the
other's; that requires:

**Each group runs its own copy of `scripts/run_bonus_series.py`
simultaneously**, each one deciding only its own agent's moves (its own
strategy, its own LLM) and submitting them only to its own server. This is
possible with **zero new tools beyond what every compliant server already
exposes**:

- `report_location` — each side's own orchestrator calls this on *both*
  servers (its own and the partner's) every turn, to learn the true
  position needed for capture detection and the visibility-radius check.
  This is legitimate here — it's the scoring/coordination layer, not a
  leak into the NL channel (the *agent's own move decision* still only
  ever sees a belief built from this, same as the base game).
- The existing message relay (`send_message`/`receive_message`) — a new
  message arriving in your own inbox is the synchronization signal "the
  opponent has moved this round," since every turn sends one. No
  separate "whose turn" tool needed.
- `sync_barriers`, `choose_action`, `start_subgame` — used exactly as in
  the base game, just by two independent processes instead of one shared
  orchestrator.

Both sides therefore **independently observe the same shared reality**
(the real network calls hitting both real servers) and arrive at the same
result on their own — confirmed by an in-process test
(`tests/agents/test_bonus_peer.py`) running both sides concurrently and
asserting they agree on the winner/totals without either one telling the
other anything.

**Tool-contract compatibility risk, explicit:** this only works if the
partner's deployed server exposes the exact tool names above with
matching signatures. If they built their own messaging/barrier-sync
tools differently, this won't interoperate without adjustment on one side
or the other — confirm compatibility before a real run.

## Algorithm / process

1. Confirm partner group; exchange the four MCP URLs and a bearer token
   for each of the partner's two servers.
2. Agree a few values that must match exactly on both sides:
   `--series-seed` (any shared string — both sides derive identical
   starting positions per sub-game from it via
   `random.Random(str((series_seed, half_index, sub_game_index)))`, so
   neither side needs to *tell* the other its starting cell — they both
   already know it), `--our-role-half1` (exact inverses of each other),
   and `config.yaml: bonus.max_draw_retries` (so a tie-retry stays in
   lockstep — each side's own `start_subgame` call cleanly resets that
   side's state for the next attempt, no extra protocol needed).
3. **Both groups run `scripts/run_bonus_series.py` at the same time**,
   each with their own role/endpoint arguments. `src.agents.bonus_peer`'s
   per-turn loop (`src.agents.bonus_peer_subgame.run_subgame_as_peer`)
   handles one sub-game; `src.agents.bonus_peer_half.run_bonus_half_as_peer`
   loops `bonus.sub_games_per_half` of those for one role assignment.
4. `src.reporting.bonus_report.build_bonus_game_json` merges each side's
   own two halves into its own copy of the Inter-Group Bonus Game JSON,
   rolling points up to **team name** (not "cop"/"thief" — that mapping
   flips between halves since roles swap).
5. `src.reporting.bonus_scoring.compute_bonus_claim` computes the 10/7/5
   bonus-points claim from the merged totals.
6. If the result is an **exact tie** (5/5, lose-lose for both groups), the
   script retries the whole series automatically, up to
   `config.yaml: bonus.max_draw_retries` times. If still tied after the
   last attempt, `config.yaml: bonus.send_email_on_draw_after_max_retries`
   decides whether to send that tied result anyway or stop — agree this
   with the partner group and set it explicitly; default `false`.
7. **Compare, don't share-and-trust.** Each side now has its own
   independently-built payload. Compare `totals_by_group`/`bonus_claim`/
   `sub_games` between the two (not the whole object — `group_1`/`group_2`
   labeling differs by whose copy it is) before either side sets
   `mutual_agreement: true` and sends.
8. **Both sides send via code, not by hand-pasting an email.** Since both
   sides already ran the full script themselves, each can call its own
   send step directly (`run_bonus_series.py --send`, gated by
   `bonus.send_on_completion`) — `scripts/send_bonus_report.py` remains
   available as a fallback for a side that, for whatever reason, didn't
   run the script itself and is instead sending an already-agreed payload
   it received from the other side.

## Constraints and limitations, alternatives considered

- A result mismatch between the two groups' emails disqualifies both groups
  for that series (0 bonus points) — cross-checking before sending is not
  optional.
- Bonus scoring: win a series = 10 pts, lose = 7 pts, exact tie = 5 pts
  each; final bonus = average across all valid series if playing multiple
  partner groups (`src.reporting.bonus_scoring.average_bonus_score`).
- **Alternative considered (the original design here, since corrected):**
  one side's orchestrator drives both agents' decisions, treating the
  partner's server as a passive validator — rejected once caught in
  review, since it never exercises the partner's own strategy/LLM at all,
  defeating the point of an inter-group competition.
- **Alternative considered:** sharing the entire codebase with the partner
  group — rejected; only the game engine/architecture may be shared, the
  agent implementation and strategy must stay unique per group (graded on
  originality).

## Edge cases

- Partner group's server goes down mid-series, or the opponent's move
  never arrives — `bonus_peer.wait_for_opponent_move` times out after
  `MAX_WAIT_SECONDS` (5 minutes) and raises; treat as a technical loss for
  that sub-game per the same rules as the base game, re-run before
  finalizing the series result.
- Disagreement discovered only after one side already sent its email — do
  not send a corrected email without re-confirming agreement with the
  partner group first; document the discrepancy.
- The Thief-side observer has no tool to query how many barriers the Cop
  side placed (`report_location` only reveals position) — `barriers_placed`
  in that side's sub-game summary is a best-effort `0`, informational
  only; it doesn't affect `winner`/points/scoring.

## Success criteria / test scenarios

- Full NL transcripts + logs proving 6 autonomous cross-group sub-games.
- Two emails (one per group) with matching JSON, captured as evidence.
- Bonus score computed and recorded in `docs/TODO.md`.

## Implementation status (Phase 7, code scaffolding done — not yet usable)

Done and tested (`tests/agents/test_bonus_{peer,runner}.py`,
`tests/reporting/test_bonus_{schema,report,scoring}.py`):
`src/agents/bonus_peer.py` + `bonus_peer_subgame.py` + `bonus_peer_half.py`
(the peer protocol — split across three files for the 150-line limit, one
logical unit), `src/agents/bonus_runner.py` (`run_one_bonus_attempt`,
plays both halves via the peer protocol and assembles the payload),
`src/reporting/bonus_{schema,report,scoring}.py` (validation, payload
merge, the 10/7/5 rule + `is_draw` + multi-partner averaging).
`scripts/run_bonus_series.py` is the entrypoint **both** groups run;
`scripts/send_bonus_report.py` is the fallback for a side sending an
already-agreed payload it didn't generate itself. Partner
URLs/tokens/team metadata are CLI arguments, never hardcoded or
committed, since no partner is identified yet and these are
per-competition, not a fixed deployment setting.

`tests/agents/test_bonus_peer.py` is the strongest evidence this design
works: it runs both sides of a sub-game/half concurrently (in-process, no
real network) and asserts they independently agree on the winner and
totals without either one telling the other anything — proving the
"both sides observe the same shared reality" property the whole
coordination model depends on.

**Still genuinely blocked on a partner group existing** — nothing above
can be exercised against a real second deployment until that happens, and
the tool-contract compatibility risk (above) can't be resolved without
knowing their actual implementation. Phase 7 stays **deferred** in
`docs/TODO.md` for that reason; this is scaffolding ready to use the
moment a partner group is identified, not a claim that the bonus has been
attempted.
