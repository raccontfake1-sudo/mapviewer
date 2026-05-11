import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# 1. إعداد الصفحة
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# 2. إضافة تنسيق CSS لتطابق شكل "AI Explanations" في الصورة تماماً
st.markdown("""
<style>
    .explanation-container {
        background-color: #111217;
        padding: 20px;
        border-radius: 10px;
    }
    .explanation-box {
        background-color: #1a1c24;
        color: #e0e0e0;
        border: 1px solid #3d3f4b;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .exp-header {
        color: #ffffff;
        font-weight: bold;
        font-size: 1.1em;
        border-bottom: 1px solid #3d3f4b;
        padding-bottom: 10px;
        margin-bottom: 15px;
    }
    .exp-label {
        color: #ffffff;
        font-weight: bold;
        display: block;
        margin-top: 15px;
    }
    .exp-content {
        color: #aeb1b7;
        line-height: 1.6;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# وظائف استخراج البيانات
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
            "commonality": str(row.get(cols["commonality"], "No data available")),
            "justification": str(row.get(cols["justification"], "No data available")),
            "differences": str(row.get(cols["differences"], "No data available"))
        })
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

def create_graph(selected_id, source_text, mappings):
    net = Network(height="600px", width="100%", bgcolor="#ffffff")
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": { "gravitationalConstant": -100, "springLength": 200 },
        "solver": "forceAtlas2Based"
      },
      "nodes": { "font": { "size": 18 }, "borderWidth": 2 },
      "edges": { "font": { "size": 14, "align": "middle" }, "smooth": false }
    }
    """)
    # العقدة المركزية فارغة كما طلبت
    net.add_node(selected_id, label=" ", title=html.escape(source_text), color="#1687d9", size=45, shape="circle")

    for idx, item in enumerate(mappings):
        net.add_node(item["mapping"], label=item["mapping"], color="#328a36", size=32, shape="circle", font={'color':'white'})
        net.add_edge(selected_id, item["mapping"], label=f"#{idx+1}", width=10-idx)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# -------------------------
# العرض الرئيسي
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    st.sidebar.title("Controls")
    selected_id = st.sidebar.selectbox("ID:", df["ECC id control"].unique())
    
    st.title("Control Mapping Viewer")
    
    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    mappings = extract_mappings(row, df)

    # 1. عرض الرسم البياني
    graph_html = create_graph(str(selected_id), str(row["Source Text"]), mappings)
    components.html(graph_html, height=650)

    # 2. عرض قسم AI Explanations (بالضبط كما في الصورة)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("## AI Explanations")
    
    for idx, m in enumerate(mappings):
        # استخدام expander لعرض الرقم والعنوان
        with st.expander(f"#{idx+1} - {m['mapping']}", expanded=(idx == 0)):
            st.markdown(f"""
            <div class="explanation-box">
                <div class="exp-header">#{idx+1} - {m['mapping']}</div>
                
                <span class="exp-label">Commonality:</span>
                <p class="exp-content">{m['commonality']}</p>
                
                <span class="exp-label">Justification:</span>
                <p class="exp-content">{m['justification']}</p>
                
                <span class="exp-label">Differences:</span>
                <p class="exp-content">{m['differences']}</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("File not found.")
