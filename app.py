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
# استخراج البيانات (مع حماية الفراغات)
# -------------------------
def clean(val):
    if pd.isna(val) or val is None:
        return "N/A"
    val = str(val).strip()
    return val if val != "" else "N/A"

def extract_mappings(row, df, top_k=10):
    results = []

    for i in range(1, 11):
        cols = get_mapping_columns(i)

        if cols["mapping"] not in df.columns:
            continue

        mapping_val = row.get(cols["mapping"])

        if pd.isna(mapping_val) or str(mapping_val).strip() == "":
            continue

        # score
        try:
            val = str(row.get(cols["final"], 0)).replace('%', '')
            score = float(val) / 100.0 if float(val) > 1 else float(val)
        except:
            score = 0.0

        results.append({
            "mapping": clean(mapping_val),
            "text": clean(row.get(cols["text"])),
            "final": score,
            "commonality": clean(row.get(cols["commonality"])),
            "justification": clean(row.get(cols["justification"])),
            "differences": clean(row.get(cols["differences"]))
        })

    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

# -------------------------
# الرسم
# -------------------------
def create_graph(selected_id, source_text, mappings):
    net = Network(height="650px", width="100%", bgcolor="#ffffff")

    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -120,
          "springLength": 200
        },
        "solver": "forceAtlas2Based",
        "stabilization": { "iterations": 1000 }
      },
      "nodes": {
        "font": { "size": 22, "face": "arial" }
      }
    }
    """)

    # 🔵 الكنترول الرئيسي
    net.add_node(
        selected_id,
        label=str(selected_id),
        title=html.escape(source_text),
        color="#1687d9",
        size=95,
        shape="circle",
        font={"color": "white", "size": 26}
    )

    # 🟢 المابينق
    for idx, item in enumerate(mappings):
        tooltip = f"""
        <div style="width:320px">
        <b>Mapping:</b> {item['mapping']}<br><br>

        <b>Text:</b><br>{item['text']}<br><br>

        <b>Score:</b> {item['final']}<br><br>

        <b>Commonality (شرح):</b><br>{item['commonality']}<br><br>

        <b>Justification:</b><br>{item['justification']}<br><br>

        <b>Differences (اختلاف):</b><br>{item['differences']}
        </div>
        """

        net.add_node(
            item["mapping"],
            label=item["mapping"],
            title=tooltip,
            color="#2e8b57",
            size=32,
            shape="circle",
            font={"color": "white", "size": 14}
        )

        net.add_edge(selected_id, item["mapping"], label=f"#{idx+1}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, "r", encoding="utf-8").read()

# -------------------------
# الواجهة
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = df.columns.str.strip()

    st.sidebar.title("Controls List")

    selected_id = st.sidebar.selectbox(
        "Select Control ID:",
        df["ECC id control"].astype(str).unique()
    )

    st.title("Control Mapping Viewer")

    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]

    mappings = extract_mappings(row, df)

    graph_html = create_graph(str(selected_id), str(row["Source Text"]), mappings)

    components.html(graph_html, height=700)

else:
    st.error("CSV file not found")
