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
    net = Network(height="700px", width="100%", bgcolor="#ffffff")

    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -140,
          "springLength": 220
        },
        "solver": "forceAtlas2Based"
      },
      "nodes": {
        "font": { "size": 20, "face": "arial" }
      },
      "edges": {
        "color": "#aaa",
        "font": { "size": 14 }
      }
    }
    """)

    # 🔵 الكنترول الرئيسي
    net.add_node(
        selected_id,
        label=str(selected_id),
        title="Control Node",
        color="#1f77b4",
        size=110,
        shape="circle",
        font={"color": "white", "size": 28, "bold": True}
    )

    # 🟢 المابينق
    for idx, item in enumerate(mappings):

        # 🔥 مهم: نعرض الشرح داخل label نفسه (مو tooltip فقط)
        label_text = f"{item['mapping']}\nScore:{item['final']:.2f}"

        tooltip = f"""
        Mapping: {item['mapping']}<br>
        Text: {item['text']}<br><br>
        Commonality:<br>{item['commonality']}<br><br>
        Justification:<br>{item['justification']}<br><br>
        Differences:<br>{item['differences']}
        """

        net.add_node(
            item["mapping"],
            label=label_text,   # 👈 هنا أهم إصلاح
            title=tooltip,
            color="#2e8b57",
            size=38,
            shape="circle",
            font={"color": "white", "size": 14}
        )

        net.add_edge(selected_id, item["mapping"], label=str(idx+1))

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
