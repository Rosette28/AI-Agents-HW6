"""Phase 4 demo entrypoint: runs one full 6-sub-game series with real
LLM-authored NL messages and belief updates, writing live state for the
Streamlit GUI (src/gui/app.py) and a human-readable transcript per
sub-game to results/transcripts/.

Prerequisite: ANTHROPIC_API_KEY set in .env (see .env.example) — this
script makes real, billed API calls and is meant to be run by hand, not
from the automated test suite.

Run: python scripts/run_llm_demo.py
Then, in another shell: streamlit run src/gui/app.py
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agents.llm_client import build_llm_client  # noqa: E402
from src.agents.orchestrator import run_series_via_mcp  # noqa: E402
from src.config.loader import load_config  # noqa: E402
from src.engine.results import save_subgame_result, save_transcript_log  # noqa: E402
from src.engine.start_positions import random_start_positions  # noqa: E402
from src.gui.state_writer import write_live_state  # noqa: E402


async def main() -> None:
    load_dotenv()
    config = load_config()

    grid_size = tuple(config["board"]["grid_size"])
    llm_client = build_llm_client(config)

    series = await run_series_via_mcp(
        grid_size=grid_size,
        max_moves=config["game"]["max_moves"],
        num_games=config["game"]["num_games"],
        max_barriers=config["game"]["max_barriers"],
        scoring=config["scoring"],
        start_positions_fn=random_start_positions,
        llm_client=llm_client,
        visibility_radius=config["observation"]["visibility_radius"],
        on_turn=write_live_state,
    )

    for index, subgame in enumerate(series["sub_games"], start=1):
        save_subgame_result(subgame, grid_size, index)
        path = save_transcript_log(subgame, grid_size, index)
        print(f"Sub-game {index}: {subgame['winner']} wins in {subgame['moves_taken']} moves "
              f"-> {path}")

    print(f"Series totals: {series['totals']}")


if __name__ == "__main__":
    asyncio.run(main())
