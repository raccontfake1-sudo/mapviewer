import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import os
import math
import html

st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# -------------------------
# Columns mapping
# -------------------------
def get_mapping_columns(i):
    suffix = "" if i == 1 else f" {i}"
    return {
        "mapping": f"NIST mapping{suffix}",
        "text": f"Text{suffix}",
        "final": f"Final Score{suffix}",
        "commonality": f"Commonality{suffix}",
        "justification": f"Justification{suffix}",
        "differences": f"Differences{suffix}"
    }


# -------------------------
# Extract mappings (Top 10)
# -------------------------
def extract_mappings(row, df, top_k=10):
    results = []

    for i in range(1, 11):
        cols = get_mapping_columns(i)

        if cols["mapping"] not in df.columns:
            continue

        if pd.isna(row.get(cols["mapping"])):
            continue

        try:
            val = str(row.get(cols["final"], 0)).replace("%", "")
            score = float(val)
            if score > 1:
                score = score / 100
        except:
            score = 0

        results.append({
            "mapping": str(row.get(cols["mapping"])),
            "text": str(row.get(cols["text"], "")),
            "final": score,
            "commonality": str(row.get(cols["commonality"], "N/A")),
            "justification": str(row.get(cols["justification"], "N/A")),
            "differences": str(row.get(cols["differences"], "N/A"))
        })

    # sort top 10
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]


# -------------------------
# Graph builder (FIXED)
# -------------------------
def create_graph(selected_id, source_text, mappings):

    net = Network(height="650px", width="100%", directed=True)

    net.set_options("""
    {
      "physics": {
        "enabled": false
      },
      "edges": {
        "arrows": {
          "to": { "enabled": true }
        },
        "color": "#b0b0b0",
        "width": 2
      },
      "nodes": {
        "shape": "circle"
      }
    }
    """)

    # 🔵 Center node
    net.add_node(
        selected_id,
        label=str(selected_id),
        title=source_text,
        color="#1565c0",
        size=80,
        font={"color": "white", "size": 25}
    )

    # 🔵 circle layout
    radius = 350
    total = max(len(mappings), 1)

    for idx, item in enumerate(mappings):

        angle = 2 * math.pi * idx / total
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)

        node_id = item["mapping"]

        net.add_node(
            node_id,
            label=str(idx + 1),
            title=html.escape(item["text"]),
            color="#1e88e5",
            size=45,
            x=x,
            y=y,
            physics=False,
            font={"color": "white", "size": 18}
        )

        net.add_edge(
            selected_id,
            node_id,
            label=str(idx + 1)
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, "r", encoding="utf-8").read()


# -------------------------
# Load data
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):

    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]

    st.sidebar.title("Controls List")

    control_ids = sorted(
        df["ECC id control"].astype(str).unique()
    )

    selected_id = st.sidebar.radio("Select Control ID:", control_ids)

    st.title("Control Mapping Viewer")

    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    mappings = extract_mappings(row, df)

    graph_html = create_graph(
        str(selected_id),
        str(row["Source Text"]),
        mappings
    )

    components.html(graph_html, height=700)

    st.markdown("## AI Explanations")

    for idx, m in enumerate(mappings):
        with st.expander(f"{idx+1} - {m['mapping']}"):
            st.write("**Commonality:**", m["commonality"])
            st.write("**Justification:**", m["justification"])
            st.write("**Differences:**", m["differences"])

else:
    st.error("Data file not found.")
