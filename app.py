import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os
import math

st.set_page_config(page_title="Control Mapping Viewer", layout="wide")


# -------------------------
# Mapping columns helper
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
# Extract mappings
# -------------------------
def extract_mappings(row, df, top_k=10):
    results = []

    for i in range(1, 11):
        cols = get_mapping_columns(i)

        if cols["mapping"] not in df.columns:
            continue

        mapping_val = row.get(cols["mapping"])
        if pd.isna(mapping_val):
            continue

        try:
            val = str(row.get(cols["final"], 0)).replace("%", "")
            score = float(val)
            if score > 1:
                score = score / 100.0
        except:
            score = 0.0

        results.append({
            "mapping": str(mapping_val),
            "text": str(row.get(cols["text"], "")),
            "final": score,
            "commonality": str(row.get(cols["commonality"], "N/A")),
            "justification": str(row.get(cols["justification"], "N/A")),
            "differences": str(row.get(cols["differences"], "N/A"))
        })

    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]


# -------------------------
# Create graph
# -------------------------
def create_graph(selected_id, source_text, mappings):

    net = Network(height="650px", width="100%", bgcolor="#ffffff")

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -120,
          "springLength": 180
        }
      },
      "nodes": {
        "borderWidth": 2,
        "font": {
          "size": 18,
          "face": "arial"
        }
      },
      "edges": {
          "color": "#c9d2dc",
          "font": {
            "size": 70,
            "align": "middle",
            "color": "#001f5c"
          }
        }
    }
    """)

    # 🔵 center node (blue big)
    net.add_node(
        selected_id,
        label=str(selected_id),
        title=html.escape(source_text),
        color="#1687d9",
        size=1200,
        shape="circle",
        physics=False,
        font={"color": "white", "size": 40}
    )

    # 🟢 green nodes
    n = len(mappings)

    for idx, item in enumerate(mappings):

        angle = (2 * math.pi / n) * idx
        x = 400 * math.cos(angle)
        y = 400 * math.sin(angle)

        net.add_node(
            item["mapping"],
            label=f"{idx+1}\n{item['mapping']}",
            title=f"Control: {item['mapping']}",
            color="#2e7d32",
            size=1000,
            shape="circle",
            x=x,
            y=y,
            physics=False,
            font={"color": "white", "size": 14}
        )

        net.add_edge(
            selected_id,
            item["mapping"],
            label=str(idx + 1),
            width=2
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

    st.sidebar.title("Controls")

    control_ids = sorted(df["ECC id control"].astype(str).unique())

    selected_id = st.sidebar.radio("Select Control ID", control_ids)

    st.title("Control Mapping Viewer")

    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    mappings = extract_mappings(row, df)

    graph_html = create_graph(
        str(selected_id),
        str(row["Source Text"]),
        mappings
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        components.html(graph_html, height=680)
    
    with col2:
        st.markdown("## AI Explanations")
    
        for idx, m in enumerate(mappings):
            with st.expander(f"{idx + 1} - {m['mapping']}"):
                st.write("**Commonality:**", m["commonality"])
                st.write("**Justification:**", m["justification"])
                st.write("**Differences:**", m["differences"])

else:
    st.error("CSV file not found")
