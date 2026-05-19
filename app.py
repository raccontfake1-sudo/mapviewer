import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

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
def clean(x):
    if pd.isna(x) or x is None:
        return "N/A"
    return str(x).strip() or "N/A"

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

        results.append({
            "mapping": clean(mapping),
            "text": clean(row.get(cols["text"])),
            "commonality": clean(row.get(cols["commonality"])),
            "justification": clean(row.get(cols["justification"])),
            "differences": clean(row.get(cols["differences"]))
        })

    return results

# -------------------------
# 🔥 FIXED GRAPH (CLEAN STRUCTURE)
# -------------------------
def create_graph(selected_id, source_text, mappings):

    net = Network(height="700px", width="100%", bgcolor="#ffffff")

    # 🚫 مهم جداً: نوقف الفيزياء (تسبب الفوضى)
    net.set_options("""
    {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "levelSeparation": 150,
          "nodeSpacing": 120
        }
      },
      "physics": {
        "enabled": false
      },
      "nodes": {
        "shape": "circle",
        "font": {
          "face": "arial",
          "color": "#000000",
          "size": 22
        }
      },
      "edges": {
        "color": "#999999",
        "font": {
          "size": 18,
          "color": "#000000",
          "align": "horizontal"
        }
      }
    }
    """)

    # 🔵 المركز
    net.add_node(
        selected_id,
        label=str(selected_id),
        title=html.escape(source_text),
        color="#1e88e5",
        size=80,
        font={"color": "#000000", "size": 28}
    )

    # 🟢 حوله بشكل مرتب
    for idx, item in enumerate(mappings, start=1):

        node_id = item["mapping"]

        net.add_node(
            node_id,
            label=str(idx),
            title=(
                f"{item['mapping']}\n\n"
                f"Text: {item['text']}\n"
                f"Commonality: {item['commonality']}\n"
                f"Justification: {item['justification']}\n"
                f"Differences: {item['differences']}"
            ),
            color="#2ecc71",
            size=40,
            font={"color": "#000000", "size": 20}
        )

        net.add_edge(
            selected_id,
            node_id,
            label=str(idx),
            width=2
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, "r", encoding="utf-8").read()

# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = df.columns.str.strip()

    st.title("Control Mapping Viewer")

    selected_id = str(df["ECC id control"].iloc[0])
    row = df[df["ECC id control"].astype(str) == selected_id].iloc[0]

    mappings = extract_mappings(row, df)

    graph_html = create_graph(selected_id, str(row["Source Text"]), mappings)

    components.html(graph_html, height=720)

else:
    st.error("CSV file not found")
