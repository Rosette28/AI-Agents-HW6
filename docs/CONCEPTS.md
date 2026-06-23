# Concepts Glossary

Every core concept this project must demonstrate, extracted from the L09
material and the assignment brief. Each entry maps the generic concept to how
it is concretely instantiated in this codebase.

## MCP (Model Context Protocol)

- **Client vs. Server.** The LLM lives only in the **Client** (the
  orchestrator in `src/agents/`). The **Server** (`src/mcp_servers/`) exposes
  Tools and Resources only — it never calls an LLM itself.
- **Tool Call flow.** Client sends the conversation state to the LLM → LLM
  returns a tool-call decision → Client invokes the tool on the MCP server →
  server executes and returns a result → Client feeds the result back to the
  LLM for the next decision.
- **Two independent servers.** One MCP server for the Cop, one for the Thief,
  each on its own port/URL, each with its own auth token. They do not talk to
  each other directly — all communication between agents is mediated by their
  respective Clients exchanging natural-language messages through tools.
- **FastMCP.** The library used to declare tools with minimal boilerplate
  (decorator-based tool registration, automatic schema generation).

## Dec-POMDP (Decentralized Partially Observable Markov Decision Process)

Formal tuple: `⟨n, S, {Ai}, P, R, {Ωi}, O, γ⟩`

- `n` — number of agents (2: Cop, Thief).
- `S` — full state space: both agents' positions + the set of barrier cells +
  move count. Neither agent observes all of `S` directly.
- `{Ai}` — per-agent action sets: movement in 8 directions (incl. diagonals)
  for both; barrier placement is Cop-only and capped at `max_barriers`.
- `P` — transition function: deterministic given a legal action (illegal
  moves, e.g. into a barrier or off-board, are rejected/no-ops).
- `R` — reward function: the scoring table (capture / survival / loss values
  in `config.yaml`).
- `{Ωi}` — per-agent observation space: each agent's local, partial view
  (its own exact position + opponent position only within
  `observation.visibility_radius`, plus whatever the opponent reveals or
  misrepresents in natural language).
- `O` — observation function: maps the true state to what each agent
  actually perceives, including the natural-language channel as a secondary,
  unreliable observation source (since the opponent may bluff).
- `γ` — discount factor, used by the Q-learning strategy module if enabled.

This project's concrete instantiation of the tuple is written out in detail
in `reports/` (Phase 6), not just restated generically.

## Partial observability

Agents never receive the opponent's exact coordinates over the wire. Belief
about the opponent's position is inferred from (a) the visibility radius
when in range, and (b) natural-language hints/claims from the opponent,
which may be truthful, vague, or deliberately misleading (bluffing).

## Multi-agent orchestration without a rigid protocol

No fixed message schema or coordinate encoding is allowed between agents.
Each agent's LLM must parse free text, extract whatever positional/intent
information it can, and decide on an action despite linguistic ambiguity.
This is the core engineering challenge analyzed in `docs/prd/nl-dialogue.md`
and the README's orchestration-analysis section.

## Q-Learning (optional strategy)

- **State (s):** agent's own position (and optionally belief about the
  opponent's position / barrier layout).
- **Action (a):** one of the 8 movement directions, or barrier placement
  (Cop only).
- **Reward (r):** intermediate shaping reward (e.g., distance closed) plus
  the terminal sub-game reward from the scoring table.
- **Epsilon-Greedy:** with probability `epsilon`, pick a random action
  (explore); otherwise pick `argmax_a Q(s,a)` (exploit). `epsilon` decays
  over episodes (`config.yaml: strategy.q_learning.epsilon_decay`).
- **Bellman update:**
  `Q(s,a) ← Q(s,a) + α[r + γ·max_a′ Q(s′,a′) − Q(s,a)]`
  where `α` = learning rate, `γ` = discount factor (both in `config.yaml`).

## Token-based authentication + revocation

Each MCP server requires a bearer token on every request. Tokens are
generated per deployment and stored only in `.env` (never committed). A
token can be revoked by rotating/removing it server-side without redeploying
the whole service, cutting off any client still presenting the old token.

## LLM deployment approaches

1. **Cloud API (chosen for this project):** Client calls a hosted LLM
   (Anthropic/OpenAI/Gemini) with an API key; routes tool-call decisions to
   the MCP server in the cloud. Simplest, no local exposure, low token cost
   for short conversations.
2. **Secured local Ollama exposed to the cloud:** requires a mandatory
   security layer (ngrok Traffic Policy, Localtonet HTTP Auth, or a hardened
   Nginx reverse proxy with TLS + htpasswd) since Ollama has no built-in auth.
3. **Hybrid:** LLM + Client stay local (e.g. via Ollama); only the MCP
   server is in the cloud. Client makes outbound-only HTTPS calls — no
   inbound ports opened, Ollama stays behind the local firewall.

This project uses **Approach 1** (see ADR in `docs/PLAN.md`).
