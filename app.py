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
def get_mapping_columns(i):
    suffix = "" if i == 1 else f" {i}"
    return {
        "mapping": f"NIST mapping{suffix}",
        "text": f"Text{suffix}",
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
# 🔥 FIXED RADIAL GRAPH (NO CHAOS)
# -------------------------
def create_graph(selected_id, source_text, mappings):

    net = Network(height="750px", width="100%", bgcolor="#ffffff")

    # ❌ مهم: إيقاف الفيزياء بالكامل
    net.set_options("""
    {
      "physics": {
        "enabled": false
      },
      "edges": {
        "color": "#888888",
        "width": 2,
        "font": {
          "size": 16,
          "color": "#000000"
        }
      },
      "nodes": {
        "shape": "circle",
        "font": {
          "face": "arial",
          "color": "#000000",
          "size": 20
        }
      }
    }
    """)

    # 🔵 المركز (ثابت)
    net.add_node(
        selected_id,
        label=str(selected_id),
        title=html.escape(source_text),
        color="#1e88e5",
        size=120,
        x=0,
        y=0,
        fixed=True,
        font={"size": 28, "color": "#000000"}
    )

    # 🟢 توزيع دائري مضبوط (IMPORTANT FIX)
    radius = 300

    n = len(mappings)

    for idx, item in enumerate(mappings, start=1):

        angle = (2 * math.pi * (idx - 1)) / n
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)

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
            size=55,
            x=x,
            y=y,
            fixed=True,
            font={"size": 22, "color": "#000000"}
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

    components.html(graph_html, height=750)

else:
    st.error("CSV file not found")
