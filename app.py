import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="Control Mapping Viewer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# CSS STYLE
# -------------------------
st.markdown("""
<style>
body { background-color: #f5f5f5; }
.block-container { padding-top: 1.5rem; padding-left: 2rem; padding-right: 1.5rem; }
[data-testid="stSidebar"] { min-width: 420px; max-width: 420px; background-color: #ffffff; border-right: 1px solid #ddd; }
.main-title { font-size: 52px; font-weight: 800; color: #2f2f2f; margin-bottom: 5px; }
.subtitle { font-size: 20px; color: #4b5563; margin-top: -5px; margin-bottom: 25px; }
.mapping-card { border: 2px solid #75b843; border-radius: 8px; background-color: #f1faec; padding: 16px; margin-bottom: 16px; }
.mapping-title { font-size: 19px; font-weight: 800; color: #1476d4; }
.rank-pill { background-color: #1476d4; color: white; border-radius: 20px; padding: 4px 12px; font-weight: 700; margin-right: 8px; }
.mapping-text { color: #444; font-size: 14.5px; line-height: 1.6; margin-top: 10px; }
.graph-box { border: 1px solid #e0e0e0; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
[data-testid="stSidebar"] div.stButton > button { width: 100%; text-align: left; padding: 12px; border-radius: 8px; border: 1px solid #eee; background-color: #fff; margin-bottom: 10px; }
.selected-control-card button { background-color: #e8f4ff !important; border: 2px solid #1476d4 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# HELPERS
# -------------------------
def short_text(text, limit=120):
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "..."

def get_mapping_columns(i):
    if i == 1: return {"mapping": "NIST mapping", "text": "Text", "final": "Final Score", "confidence": "Confidence match"}
    return {"mapping": f"NIST mapping {i}", "text": f"Text {i}", "final": f"Final Score {i}", "confidence": f"Confidence match {i}"}

def extract_mappings(row, df, top_k):
    results = []
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        if cols["mapping"] not in df.columns or pd.isna(row.get(cols["mapping"])): continue
        try:
            val = str(row.get(cols["final"], 0)).replace('%', '')
            final_score = float(val) if val else 0.0
            if final_score > 1.0: final_score = final_score / 100.0
        except: final_score = 0.0
        results.append({
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "final": final_score,
            "confidence": str(row.get(cols["confidence"], "N/A"))
        })
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

def create_graph(selected_control, source_text, mappings):
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#333")
    
    # إعدادات الخطوط والدوائر لتظهر الأرقام بوضوح
    net.set_options("""
    {
      "nodes": {
        "font": {"size": 18, "face": "arial", "vadjust": -2},
        "borderWidth": 2
      },
      "physics": {
        "forceAtlas2Based": {"gravitationalConstant": -60, "centralGravity": 0.01, "springLength": 130},
        "solver": "forceAtlas2Based"
      }
    }
    """)

    # العقدة المركزية (الضابط)
    net.add_node(selected_control, label=selected_control, title=html.escape(source_text), 
                 color="#1687d9", size=45, shape="circle", font={'color': 'white', 'size': 24, 'bold': True})

    # العقد المحيطة (النسب المئوية داخل الدوائر)
    for item in mappings:
        score_percent = f"{item['final'] * 100:.0f}%"
        node_color = "#328a36" if item["final"] >= 0.85 else "#5a9e5d"
        
        # نضع النسبة المئوية كـ label لتظهر داخل الدائرة
        # ونضع اسم الكود (مثلاً GV.PO-01) كـ title ليظهر عند تمرير الماوس
        net.add_node(item["mapping"], 
                     label=score_percent, 
                     title=f"Code: {item['mapping']}\n{item['text']}", 
                     color={"background": node_color, "border": "#246628"}, 
                     size=30, 
                     shape="circle", 
                     font={'color': 'white', 'bold': True})
        
        net.add_edge(selected_control, item["mapping"], color="#d1d5db", width=1.5)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, "r", encoding="utf-8") as f: return f.read()

# -------------------------
# DATA LOADING
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
else:
    st.error("Missing Data File"); st.stop()

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.markdown('<div class="sidebar-title">ECC Controls</div>', unsafe_allow_html=True)
search_query = st.sidebar.text_input("🔍 Search ID...", placeholder="e.g. 1.1")
filtered_df = df[df["ECC id control"].astype(str).str.contains(search_query, case=False)] if search_query else df

if "selected_id" not in st.session_state: st.session_state.selected_id = str(df["ECC id control"].iloc[0])

with st.sidebar.container(height=650):
    for idx, row_data in filtered_df.iterrows():
        cid = str(row_data["ECC id control"])
        if st.button(f"📌 {cid}\n{short_text(row_data['Source Text'])}", key=f"btn_{cid}_{idx}"):
            st.session_state.selected_id = cid; st.rerun()

# -------------------------
# MAIN CONTENT
# -------------------------
selected_row = df[df["ECC id control"].astype(str) == st.session_state.selected_id].iloc[0]
mappings = extract_mappings(selected_row, df, top_k=12)

st.markdown('<div class="main-title">Control Mapping Viewer</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Viewing Control: <b>{st.session_state.selected_id}</b></div>', unsafe_allow_html=True)

col_graph, col_list = st.columns([3, 2])

with col_graph:
    st.markdown("### 🕸️ Visual Mapping")
    html_data = create_graph(st.session_state.selected_id, str(selected_row["Source Text"]), mappings)
    components.html(html_data, height=620)

with col_list:
    st.markdown("### 🏆 Top Recommendations")
    with st.container(height=620):
        for idx, item in enumerate(mappings):
            st.markdown(f"""
            <div class="mapping-card">
                <span class="rank-pill">#{idx+1}</span>
                <span class="mapping-title">{item['mapping']} - {item['final']*100:.0f}%</span>
                <div class="mapping-text">{item['text']}</div>
            </div>
            """, unsafe_allow_html=True)
