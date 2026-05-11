import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# -------------------------
# 1. إعدادات الصفحة والتصميم (CSS)
# -------------------------
st.set_page_config(page_title="Control Mapping Viewer", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-title { font-size: 36px; font-weight: 800; color: #2f2f2f; margin-bottom: 10px; }
    .subtitle { font-size: 18px; color: #666; margin-bottom: 20px; }
    /* تنسيق صندوق التفسيرات الداكن */
    .explanation-box {
        background-color: #1e1e1e; 
        padding: 20px; 
        border-radius: 10px; 
        color: #dcdcdc; 
        border-left: 6px solid #1476d4;
        margin-bottom: 10px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .exp-label { color: #58a6ff; font-weight: bold; font-size: 16px; margin-top: 10px; display: block; }
    .exp-content { font-size: 14.5px; line-height: 1.6; color: #e0e0e0; margin-bottom: 12px; }
    
    /* تحسين شكل القائمة الجانبية */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #ddd; }
    div.stButton > button {
        width: 100%; height: auto; text-align: left; padding: 15px;
        border-radius: 8px; border: 1px solid #eee; background-color: white;
        margin-bottom: 5px; transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #eaf6ff; border-color: #1476d4; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# 2. وظائف معالجة البيانات
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

def extract_mappings(row, df):
    results = []
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        if cols["mapping"] not in df.columns or pd.isna(row.get(cols["mapping"])):
            continue
        
        # استخراج القيم مع معالجة النسب المئوية
        try:
            val = str(row.get(cols["final"], 0)).replace('%', '')
            score = float(val) / 100.0 if float(val) > 1.0 else float(val)
        except: score = 0.0

        results.append({
            "rank": i,
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "final": score,
            "commonality": str(row.get(cols["commonality"], "N/A")),
            "justification": str(row.get(cols["justification"], "N/A")),
            "differences": str(row.get(cols["differences"], "N/A"))
        })
    # ترتيب حسب السكور النهائي
    return sorted(results, key=lambda x: x["final"], reverse=True)

# -------------------------
# 3. بناء الرسم البياني (Pyvis)
# -------------------------
def create_styled_graph(selected_id, source_text, mappings):
    net = Network(height="600px", width="100%", bgcolor="#ffffff", directed=False)
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": { "gravitationalConstant": -60, "centralGravity": 0.01, "springLength": 120, "springConstant": 0.08 },
        "solver": "forceAtlas2Based", "stabilization": { "iterations": 100 }
      },
      "nodes": { "font": { "face": "arial" }, "borderWidth": 2 },
      "edges": { "smooth": false }
    }
    """)
    
    # العقدة المركزية (الضابط المختار)
    net.add_node(selected_id, label=selected_id, title=html.escape(source_text), 
                 color="#1687d9", size=45, font={'size': 25, 'color': 'white', 'bold': True})

    for item in mappings:
        # العقد المحيطة
        net.add_node(item["mapping"], label=item["mapping"], title=html.escape(item["text"]), 
                     color="#328a36", size=30, font={'size': 18, 'color': 'white'})
        
        # السهم مع رقم الترتيب (مثل #1, #2 كما في الصورة)
        net.add_edge(selected_id, item["mapping"], label=f"#{item['rank']}", 
                     width=2, color="#dcd2d2", 
                     font={'align': 'middle', 'size': 16, 'color': '#1476d4', 'strokeWidth': 2, 'strokeColor': '#ffffff'})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# -------------------------
# 4. الواجهة الرئيسية
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    # القائمة الجانبية للاختيار
    st.sidebar.title("Controls List")
    search = st.sidebar.text_input("Search ID:", placeholder="e.g. 1.1")
    
    filtered_df = df
    if search:
        filtered_df = df[df["ECC id control"].astype(str).str.contains(search)]

    # إدارة الحالة لاختيار الضابط
    if "selected_id" not in st.session_state:
        st.session_state.selected_id = str(df["ECC id control"].iloc[0])

    for _, r in filtered_df.iterrows():
        label = f"ID: {r['ECC id control']}\n{str(r['Source Text'])[:50]}..."
        if st.sidebar.button(label, key=f"btn_{r['ECC id control']}"):
            st.session_state.selected_id = str(r["ECC id control"])

    # جلب بيانات الضابط المختار
    current_id = st.session_state.selected_id
    row_data = df[df["ECC id control"].astype(str) == current_id].iloc[0]
    mappings = extract_mappings(row_data, df)

    # العرض الرئيسي
    st.markdown(f'<div class="main-title">Control Mapping Viewer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">Viewing: <b>{current_id}</b></div>', unsafe_allow_html=True)

    col_graph, col_info = st.columns([1.5, 1])

    with col_graph:
        st.write("### Visual Mapping")
        graph_html = create_styled_graph(current_id, str(row_data["Source Text"]), mappings)
        components.html(graph_html, height=620)

    with col_info:
        st.write("### 🤖 AI Explanations")
        info_container = st.container(height=600)
        with info_container:
            for m in mappings:
                with st.expander(f"**#{m['rank']} - {m['mapping']}**", expanded=(m['rank'] == 1)):
                    st.markdown(f"""
                    <div class="explanation-box">
                        <span class="exp-label">Commonality:</span>
                        <p class="exp-content">{m['commonality']}</p>
                        
                        <span class="exp-label">Justification:</span>
                        <p class="exp-content">{m['justification']}</p>
                        
                        <span class="exp-label">Differences:</span>
                        <p class="exp-content">{m['differences']}</p>
                    </div>
                    """, unsafe_allow_html=True)
else:
    st.error(f"File '{DATA_FILE}' not found. Please upload it to the directory.")
