Import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# إعداد الصفحة
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# -------------------------
# CSS STYLE - لتطابق شكل التفسيرات في الصورة
# -------------------------
st.markdown("""
<style>
    .explanation-box {
        background-color: #1a1c24;
        color: #e0e0e0;
        border: 1px solid #3d3f4b;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .exp-title { color: #ffffff; font-weight: bold; font-size: 1.1em; margin-bottom: 10px; }
    .exp-label { color: #9da0a9; font-weight: bold; margin-top: 10px; display: block; }
    .exp-text { margin-bottom: 10px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# وظائف معالجة البيانات
# -------------------------
def get_mapping_columns(i):
    # نأخذ الأعمدة الأساسية بالإضافة لأعمدة التفسير (AI Explanations)
    suffix = "" if i == 1 else f" {i}"
    return {
        "mapping": f"NIST mapping{suffix}",
        "text": f"Text{suffix}",
        "final": f"Final Score{suffix}",
        "commonality": f"Commonality{suffix}",
        "justification": f"Justification{suffix}",
        "differences": f"Differences{suffix}"
    }

def extract_mappings(row, df, top_k=10):
    results = []
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        if cols["mapping"] not in df.columns or pd.isna(row.get(cols["mapping"])): continue
        try:
            val = str(row.get(cols["final"], 0)).replace('%', '')
            score = float(val) / 100.0 if float(val) > 1.0 else float(val)
        except: score = 0.0
        
        results.append({
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "final": score,
            "commonality": str(row.get(cols["commonality"], "N/A")),
            "justification": str(row.get(cols["justification"], "N/A")),
            "differences": str(row.get(cols["differences"], "N/A"))
        })
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

def create_graph(selected_id, source_text, mappings):
    net = Network(height="650px", width="100%", bgcolor="#ffffff")
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": { "gravitationalConstant": -100, "springLength": 200 },
        "solver": "forceAtlas2Based", "stabilization": { "iterations": 1000 }
      },
      "nodes": { "font": { "size": 18, "face": "arial" }, "borderWidth": 2 },
      "edges": { "font": { "size": 16, "align": "middle", "color": "#1476d4" }, "color": "#d3dbe3" }
    }
    """)
    # العقدة المركزية بدون رقم في الوسط كما طلبت
    net.add_node(selected_id, label=" ", color="#1687d9", size=45, shape="circle")

    for idx, item in enumerate(mappings):
        edge_width = 10 - idx
        net.add_node(item["mapping"], label=item["mapping"], color="#328a36", size=32, shape="circle", font={'color':'white'})
        net.add_edge(selected_id, item["mapping"], label=f"#{idx+1}", width=edge_width)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# -------------------------
# الواجهة الرئيسية
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    st.sidebar.title("Controls List")
    selected_id = st.sidebar.selectbox("Select Control ID:", df["ECC id control"].unique())
    
    st.title("Control Mapping Viewer")
    
    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    mappings = extract_mappings(row, df)

    # 1. عرض الرسم البياني (طبق الأصل)
    graph_html = create_graph(str(selected_id), str(row["Source Text"]), mappings)
    components.html(graph_html, height=680)

    # 2. عرض قسم التفسيرات (AI Explanations) بنفس شكل الصورة
    st.markdown("## AI Explanations")
    for idx, m in enumerate(mappings):
        with st.expander(f"#{idx+1} - {m['mapping']}", expanded=(idx == 0)):
            st.markdown(f"""
            <div class="explanation-box">
                <span class="exp-label">Commonality:</span>
                <div class="exp-text">{m['commonality']}</div>
                
                <span class="exp-label">Justification:</span>
                <div class="exp-text">{m['justification']}</div>
                
                <span class="exp-label">Differences:</span>
                <div class="exp-text">{m['differences']}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("Data file not found.")
