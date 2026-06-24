"""Real-time Streamlit GUI (Phase 4) — polls the JSON state file written by
`src/gui/state_writer.write_live_state` (wired into the orchestrator's
`on_turn` callback by `scripts/run_llm_demo.py`) and re-renders the grid,
agent positions, barriers, and each agent's belief/last message.

Run: streamlit run src/gui/app.py
"""

import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.gui.state_writer import read_live_state  # noqa: E402

_POLL_INTERVAL_SECONDS = 1.0


def _render_grid(snapshot: dict) -> str:
    """Build an HTML table for the board: C=Cop, T=Thief, #=barrier."""
    rows, cols = snapshot["rows"], snapshot["cols"]
    barriers = {tuple(b) for b in snapshot["barriers"]}
    cop_pos = tuple(snapshot["cop_pos"])
    thief_pos = tuple(snapshot["thief_pos"])

    html = ["<table style='border-collapse:collapse'>"]
    for r in range(rows):
        html.append("<tr>")
        for c in range(cols):
            cell = (r, c)
            if cell == cop_pos:
                label, color = "C", "#fca5a5"
            elif cell == thief_pos:
                label, color = "T", "#93c5fd"
            elif cell in barriers:
                label, color = "#", "#374151"
            else:
                label, color = "", "#f3f4f6"
            html.append(
                f"<td style='width:36px;height:36px;text-align:center;"
                f"border:1px solid #999;background:{color}'>{label}</td>"
            )
        html.append("</tr>")
    html.append("</table>")
    return "".join(html)


def main() -> None:
    st.set_page_config(page_title="Cops and Robbers — Live", layout="wide")
    st.title("Cops and Robbers — Live Game State")

    placeholder = st.empty()
    while True:
        snapshot = read_live_state()
        with placeholder.container():
            if snapshot is None:
                st.info("No run in progress yet — start scripts/run_llm_demo.py.")
            else:
                st.markdown(f"**Move {snapshot['move_number']}** — "
                            f"barriers placed: {snapshot['barriers_placed']}")
                st.markdown(_render_grid(snapshot), unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                for col, agent in ((col1, "cop"), (col2, "thief")):
                    with col:
                        st.subheader(agent.upper())
                        st.write("Last message:", snapshot["last_messages"].get(agent, ""))
                        belief = snapshot["beliefs"].get(agent)
                        if belief:
                            st.write("Belief:", belief["note"], f"(confidence: {belief['confidence']})")
        time.sleep(_POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
