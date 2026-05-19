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
# تنظيف
# -------------------------
def clean(x):
    if pd.isna(x) or x is None:
        return "N/A"
    x = str(x).strip()
    return x if x else "N/A"

# -------------------------
# استخراج المابينق
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
# الرسم
# -------------------------
def create_graph(selected_id, source_text, mappings):

    net = Network(height="700px", width="100%", bgcolor="#ffffff")

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "solver": "forceAtlas2Based"
      },
      "nodes": {
        "shape": "circle",
        "font": {
          "face": "arial",
          "color": "#000000",
          "size": 30
        },
        "borderWidth": 3
      },
      "edges": {
        "color": "#999999",
        "font": {
          "size": 22,
          "color": "#000000",
          "bold": true
        }
      }
    }
    """)

    # 🔵 العقدة الرئيسية
    net.add_node(
        selected_id,
        label=str(selected_id),
        title=html.escape(source_text),
        color="#1e90ff",
        size=220,
        font={"color": "#000000", "size": 45},
        physics=False
    )

    # 🟢 العقد الفرعية
    for idx, item in enumerate(mappings, start=1):

        net.add_node(
            item["mapping"],
            label=f"{idx}",
            title=f"""
Text: {item['text']}
Commonality: {item['commonality']}
Justification: {item['justification']}
Differences: {item['differences']}
""",
            color="#2ecc71",
            size=60,
            font={"color": "#000000", "size": 28}
        )

        net.add_edge(
            selected_id,
            item["mapping"],
            label=str(idx),
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

    st.title("Control Mapping Viewer")

    # ❌ بدون search box — ناخذ أول كنترول تلقائياً
    selected_id = str(df["ECC id control"].iloc[0])
    row = df[df["ECC id control"].astype(str) == selected_id].iloc[0]

    mappings = extract_mappings(row, df)

    graph_html = create_graph(
        selected_id,
        str(row["Source Text"]),
        mappings
    )

    components.html(graph_html, height=750)

    # -------------------------
    # 📊 شرح الكنترول
    # -------------------------
    st.markdown("## 📌 Control Explanation")

    for i, m in enumerate(mappings, start=1):
        st.markdown(f"""
### {i}. {m['mapping']}

- **Commonality:** {m['commonality']}
- **Justification:** {m['justification']}
- **Differences:** {m['differences']}
""")

else:
    st.error("CSV file not found")
