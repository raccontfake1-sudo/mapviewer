import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# --- إعداد الصفحة ---
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# --- تنسيق الـ CSS لتطابق شكل البيانات في الصورة (AI Explanations) ---
st.markdown("""
<style>
    .main-title { color: #ffffff; font-size: 2.2em; font-weight: bold; margin-bottom: 20px; }
    .explanation-container { background-color: #0e1117; padding: 10px; border-radius: 10px; }
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
        margin-bottom: 15px;
        display: block;
    }
    .exp-label { color: #ffffff; font-weight: bold; display: block; margin-top: 15px; font-size: 1em; }
    .exp-content { color: #aeb1b7; line-height: 1.6; margin-bottom: 10px; font-size: 0.95em; }
</style>
""", unsafe_allow_html=True)

# --- وظائف معالجة البيانات ---
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
        
        # معالجة السكور للترتيب
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
    return sorted(results, key=lambda x: x["final"], reverse=True)

def create_styled_graph(selected_id, source_text, mappings):
    net = Network(height="600px", width="100%", bgcolor="#ffffff")
    net.set_options("""
    {
      "physics": { "forceAtlas2Based": { "gravitationalConstant": -100, "springLength": 200 }, "solver": "forceAtlas2Based" },
      "nodes": { "font": { "size": 18, "face": "arial" }, "borderWidth": 2 },
      "edges": { "font": { "size": 14, "align": "middle", "color": "#1476d4" }, "color": "#d3dbe3", "smooth": false }
    }
    """)
    
    # العقدة المركزية (دائرة فارغة بدون نص داخلي)
    net.add_node(selected_id, label=" ", title=html.escape(source_text), color="#1687d9", size=45, shape="circle")

    # إضافة العقد المحيطة والأسهم المرقمة
    for idx, item in enumerate(mappings):
        rank = idx + 1
        edge_thickness = 10 - idx # الخط الأقرب أسمك
        net.add_node(item["mapping"], label=item["mapping"], color="#328a36", size=32, shape="circle", font={'color':'white'})
        net.add_edge(selected_id, item["mapping"], label=f"#{rank}", width=edge_thickness)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# --- البرنامج الرئيسي ---
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    # القائمة الجانبية
    st.sidebar.markdown("### Controls Selection")
    selected_id = st.sidebar.selectbox("Select ID:", df["ECC id control"].unique())
    
    # جلب بيانات الصف المختار
    row_data = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    all_mappings = extract_all_data(row_data, df)

    # عنوان الصفحة
    st.markdown(f'<div class="main-title">Control Mapping Viewer</div>', unsafe_allow_html=True)
    st.write(f"Viewing: **{selected_id}**")

    # 1. عرض الرسم البياني
    graph_html = create_styled_graph(str(selected_id), str(row_data["Source Text"]), all_mappings)
    components.html(graph_html, height=620)

    # 2. عرض قسم AI Explanations (البيانات كاملة)
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.markdown('<div class="main-title" style="font-size: 1.8em;">AI Explanations</div>', unsafe_allow_html=True)
    
    for idx, m in enumerate(all_mappings):
        # استخدام Expander لعرض البيانات بشكل منظم كما في الصورة
        with st.expander(f"#{idx+1} - {m['mapping']}", expanded=(idx == 0)):
            st.markdown(f"""
            <div class="explanation-box">
                <span class="exp-header">#{idx+1} - {m['mapping']}</span>
                
                <span class="exp-label">Commonality:</span>
                <p class="exp-content">{m['commonality']}</p>
                
                <span class="exp-label">Justification:</span>
                <p class="exp-content">{m['justification']}</p>
                
                <span class="exp-label">Differences:</span>
                <p class="exp-content">{m['differences']}</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("لم يتم العثور على ملف البيانات CSV. تأكد من وجوده في نفس المجلد.")
