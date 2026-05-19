import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# -------------------------
# Columns
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
# Clean
# -------------------------
def clean(x):
    if pd.isna(x) or x is None:
        return "N/A"
    return str(x).strip() or "N/A"

# -------------------------
# Extract
# -------------------------
def extract_mappings(row, df):
    results = []

    for i in range(1, 11):
        cols = get_mapping_columns(i)

        if cols["mapping"] not in df.columns:
            continue

        mapping = row.get(cols["mapping"])
        if pd.isna(mapping) or str(mapping).strip() == "":
            continue

        try:
            score = float(str(row.get(cols["final"], 0)).replace("%", ""))
            if score > 1:
                score = score / 100
        except:
            score = 0.0

        results.append({
            "mapping": clean(mapping),
            "text": clean(row.get(cols["text"])),
            "commonality": clean(row.get(cols["commonality"])),
            "justification": clean(row.get(cols["justification"])),
            "differences": clean(row.get(cols["differences"]))
        })

    return results

# -------------------------
# Graph (FIXED + balanced)
# -------------------------
def create_graph(selected_id, source_text, mappings):

    net = Network(height="650px", width="100%", bgcolor="#ffffff")

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "solver": "barnesHut",
        "barnesHut": {
          "gravitationalConstant": -8000,
          "springLength": 160,
          "springConstant": 0.04
        }
      },
      "nodes": {
        "shape": "circle",
        "font": {
          "face": "arial",
          "color": "#000000",
          "size": 22
        },
        "borderWidth": 2
      },
      "edges": {
        "color": "#999999",
        "font": {
          "size": 18,
          "color": "#000000",
          "bold": true
        }
      }
    }
    """)

    # 🔵 Main node (moderate size)
    net.add_node(
        selected_id,
        label=str(selected_id),
        title=html.escape(source_text),
        color="#1e88e5",
        size=90,
        font={"color": "#000000", "size": 30},
        physics=False
    )

    # 🟢 child nodes (small & clean)
    for idx, item in enumerate(mappings, start=1):

        net.add_node(
            item["mapping"],
            label=item["mapping"],
            title=f"{item['text']}\n\nCommonality: {item['commonality']}\nJustification: {item['justification']}\nDifferences: {item['differences']}",
            color="#2ecc71",
            size=35,
            font={"color": "#000000", "size": 18}
        )

        # 🔢 edge numbers ONLY
        net.add_edge(
            selected_id,
            item["mapping"],
            label=str(idx),
            width=2
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, "r", encoding="utf-8").read()

# -------------------------
# UI (NO SEARCH BOX)
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = df.columns.str.strip()

    st.title("Control Mapping Viewer")

    # أول كنترول فقط
    selected_id = str(df["ECC id control"].iloc[0])
    row = df[df["ECC id control"].astype(str) == selected_id].iloc[0]

    mappings = extract_mappings(row, df)

    graph_html = create_graph(selected_id, str(row["Source Text"]), mappings)

    components.html(graph_html, height=700)

else:
    st.error("CSV file not found")
