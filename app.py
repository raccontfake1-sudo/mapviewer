import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# --- 1. إعداد الصفحة وتنسيق المظهر (CSS) ---
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

st.markdown("""
<style>
    /* تنسيق الحاوية الرئيسية للتفسيرات */
    .explanation-box {
        background-color: #1a1c24;
        color: #e0e0e0;
        border: 1px solid #3d3f4b;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    /* تنسيق العناوين الجانبية (Commonality, etc.) */
    .exp-label {
        color: #ffffff;
        font-weight: bold;
        display: block;
        margin-top: 15px;
        font-size: 1.05em;
    }
    /* تنسيق المحتوى النصي */
    .exp-content {
        color: #aeb1b7;
        line-height: 1.6;
        margin-bottom: 10px;
        font-size: 0.95em;
        text-align: justify;
    }
    /* تنسيق عنوان الصندوق الداخلي */
    .internal-header {
        color: #ffffff;
        font-weight: bold;
        border-bottom: 1px solid #3d3f4b;
        padding-bottom: 10px;
        margin-bottom: 15px;
        font-size: 1.1em;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. وظائف استخراج البيانات من CSV ---
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

def extract_all_data(row, df):
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
    # ترتيب المmapping بناءً على السكور (الأعلى أولاً)
    return sorted(results, key=lambda x: x["final"], reverse=True)

# --- 3. بناء الرسم البياني (بدون رقم في المنتصف) ---
def create_styled_graph(selected_id, source_text, mappings):
    net = Network(height="600px", width="100%", bgcolor="#ffffff")
    net.set_options("""
    {
      "physics": { "forceAtlas2Based": { "gravitationalConstant": -100, "springLength": 200 }, "solver": "forceAtlas2Based" },
      "nodes": { "font": { "size": 18, "face": "arial" }, "borderWidth": 2 },
      "edges": { "font": { "size": 14, "align": "middle", "color": "#1476d4" }, "color": "#d3dbe3", "smooth": false }
    }
    """)
    
    # العقدة المركزية: نص فارغ " " لإخفاء الرقم 1.1
    net.add_node(selected_id, label=" ", title=html.escape(source_text), color="#1687d9", size=45, shape="circle")

    for idx, item in enumerate(mappings):
        rank = idx + 1
        # سمك الخط يتدرج من الأقرب (أسمك) إلى الأبعد (أنحف)
        edge_thickness = 10 - idx if (10 - idx) > 1 else 1
        net.add_node(item["mapping"], label=item["mapping"], color="#328a36", size=32, shape="circle", font={'color':'white'})
        net.add_edge(selected_id, item["mapping"], label=f"#{rank}", width=edge_thickness)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# --- 4. تشغيل التطبيق ---
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    st.sidebar.title("Controls")
    selected_id = st.sidebar.selectbox("Select Control ID:", df["ECC id control"].unique())
    
    row_data = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    all_mappings = extract_all_data(row_data, df)

    st.title("Control Mapping Viewer")
    st.write(f"Viewing Context for: **{selected_id}**")

    # عرض الرسم البياني
    graph_html = create_styled_graph(str(selected_id), str(row_data["Source Text"]), all_mappings)
    components.html(graph_html, height=620)

    # عرض قسم التفسيرات AI Explanations
    st.markdown("<br><h2 style='color: white;'>AI Explanations</h2>", unsafe_allow_html=True)
    
    for idx, m in enumerate(all_mappings):
        # استخدام st.expander لجعل الواجهة نظيفة وقابلة للطي
        with st.expander(f"#{idx+1} - {m['mapping']}", expanded=(idx == 0)):
            # عرض البيانات داخل حاوية CSS المنسقة
            st.markdown(f"""
            <div class="explanation-box">
                <div class="internal-header">#{idx+1} - {m['mapping']}</div>
                
                <span class="exp-label">Commonality:</span>
                <p class="exp-content">{m['commonality']}</p>
                
                <span class="exp-label">Justification:</span>
                <p class="exp-content">{m['justification']}</p>
                
                <span class="exp-label">Differences:</span>
                <p class="exp-content">{m['differences']}</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("File 'final_ontology_refined_mappings_with_explanations.csv' not found.")
