import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# -------------------------
# الأعمدة
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
# تنظيف البيانات
# -------------------------
def clean(x):
    if pd.isna(x) or x is None:
        return "N/A"
    x = str(x).strip()
    return x if x != "" else "N/A"

# -------------------------
# استخراج
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
            "final": score,
            "commonality": clean(row.get(cols["commonality"])),
            "justification": clean(row.get(cols["justification"])),
            "differences": clean(row.get(cols["differences"]))
        })

    return sorted(results, key=lambda x: x["final"], reverse=True)

# -------------------------
# الرسم (FIXED)
# -------------------------
def create_graph(selected_id, source_text, mappings):
    net = Network(height="650px", width="100%", bgcolor="#ffffff")

    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -100,
          "springLength": 200
        },
        "solver": "forceAtlas2Based",
        "stabilization": {
          "iterations": 1000
        }
      },
      "nodes": {
        "font": {
          "size": 18,
          "face": "arial"
        },
        "borderWidth": 2
      },
      "edges": {
        "font": {
          "size": 16,
          "align": "middle",
          "color": "#1476d4"
        },
        "color": "#d3dbe3"
      }
    }
    """)

    # الدائرة الزرقاء الرئيسية
    net.add_node(
        selected_id,
        label=str(selected_id),
        title=html.escape(source_text),
        color="#1687d9",
        size=180,
        shape="circle",
        physics=False,
        font={
            "color": "white",
            "size": 50
        }
    )

    # الدوائر الخضراء
    for idx, item in enumerate(mappings):

        net.add_node(
            item["mapping"],
            label=item["mapping"],
            title=html.escape(item["text"]),
            color="#328a36",
            size=45,
            shape="circle",
            font={
                "color": "white",
                "size": 20
            }
        )

        net.add_edge(
            selected_id,
            item["mapping"],
            label=f"{idx + 1}",
            width=3
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, "r", encoding="utf-8").read()
# -------------------------
# UI
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = df.columns.str.strip()

    st.sidebar.title("Controls")

    selected_id = st.sidebar.selectbox(
        "Select Control ID",
        df["ECC id control"].astype(str).unique()
    )

    st.title("Control Mapping Viewer")

    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]

    mappings = extract_mappings(row, df)

    graph_html = create_graph(
        str(selected_id),
        str(row["Source Text"]),
        mappings
    )

    components.html(graph_html, height=720)

else:
    st.error("CSV file not found")
