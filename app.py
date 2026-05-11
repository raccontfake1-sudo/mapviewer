import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# 1. إعدادات الصفحة - جعلها عريضة جداً
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# -------------------------
# CSS STYLE - تحسين المظهر وزيادة الوضوح
# -------------------------
st.markdown("""
<style>
    /* تقليل الهوامش العلوية والجانبية لزيادة مساحة العرض */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    
    /* تنسيق الكروت الجانبية */
    .mapping-card { 
        border: 2px solid #75b843; 
        border-radius: 10px; 
        background-color: #f1faec; 
        padding: 18px; 
        margin-bottom: 12px; 
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .rank-pill { 
        background-color: #1476d4; 
        color: white; 
        border-radius: 20px; 
        padding: 3px 12px; 
        font-weight: bold; 
        font-size: 0.9em;
    }
    h1 { font-size: 2.5rem !important; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# HELPERS
# -------------------------
def get_mapping_columns(i):
    if i == 1: return {"mapping": "NIST mapping", "text": "Text", "final": "Final Score"}
    return {"mapping": f"NIST mapping {i}", "text": f"Text {i}", "final": f"Final Score {i}"}

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
            "final": score
        })
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

def create_graph(selected_id, source_text, mappings):
    # زيادة الطول (Height) ليكون الرسم أكبر عمودياً
    net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="#333")
    
    # تحسين إعدادات الفيزياء لجعل الدوائر تبتعد عن بعضها وتصبح أوضح
    net.set_options("""
    {
      "nodes": {
        "font": { "size": 20, "face": "arial", "vadjust": -2 },
        "borderWidth": 3,
        "shadow": true
      },
      "edges": {
        "font": { "size": 16, "align": "middle", "color": "#2eb086", "strokeWidth": 3, "strokeColor": "#ffffff" },
        "color": { "color": "#cccccc", "highlight": "#1687d9" },
        "width": 3,
        "smooth": { "type": "continuous" }
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -150,
          "centralGravity": 0.005,
          "springLength": 200,
          "springConstant": 0.1
        },
        "solver": "forceAtlas2Based",
        "stabilization": { "enabled": true, "iterations": 200 }
      }
    }
    """)

    # العقدة المركزية (أكبر وأوضح)
    net.add_node(selected_id, label=selected_id, title=html.escape(source_text), 
                 color="#1687d9", size=55, shape="circle", 
                 font={'color':'white', 'size': 26, 'bold':True})

    for item in mappings:
        score_val = int(item["final"] * 100)
        label_type = "PRIMARY" if score_val >= 88 else "SECONDARY"
        edge_label = f"{label_type}\n{score_val}%"
        
        # العقد الفرعية (أكبر)
        net.add_node(item["mapping"], label=item["mapping"], title=html.escape(item["text"]), 
                     color="#328a36", size=35, shape="circle", 
                     font={'color':'white', 'size': 18})
        
        net.add_edge(selected_id, item["mapping"], label=edge_label)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# -------------------------
# MAIN LOGIC
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    # القائمة الجانبية
    st.sidebar.title("ECC Controls List")
    search = st.sidebar.text_input("🔍 Search Control ID...", "")
    filtered_df = df[df["ECC id control"].astype(str).str.contains(search)] if search else df
    
    if "selected_id" not in st.session_state: 
        st.session_state.selected_id = str(df["ECC id control"].iloc[0])
    
    with st.sidebar.container(height=600):
        for cid in filtered_df["ECC id control"].unique():
            is_selected = "✅" if str(cid) == st.session_state.selected_id else "📌"
            if st.button(f"{is_selected} {cid}", key=f"btn_{cid}"):
                st.session_state.selected_id = str(cid)
                st.rerun()

    # جلب البيانات للعنصر المختار
    row = df[df["ECC id control"].astype(str) == st.session_state.selected_id].iloc[0]
    mappings = extract_mappings(row, df)

    st.title("Control Mapping Viewer")
    
    # تقسيم الصفحة: الرسم البياني يأخذ مساحة أكبر (70%) والقائمة (30%)
    col_graph, col_list = st.columns([7, 3])

    with col_graph:
        st.subheader(f"Visual Mapping for: {st.session_state.selected_id}")
        graph_html = create_graph(st.session_state.selected_id, str(row["Source Text"]), mappings)
        # زيادة الارتفاع هنا لضمان الوضوح
        components.html(graph_html, height=800)

    with col_list:
        st.subheader("Top Recommendations")
        with st.container(height=780):
            for idx, m in enumerate(mappings):
                st.markdown(f"""
                <div class="mapping-card">
                    <span class="rank-pill">#{idx+1}</span> <b>{m['mapping']}</b>
                    <div style='margin-top:8px; font-weight:bold; color:#1687d9;'>Score: {int(m['final']*100)}%</div>
                    <p style='font-size:13px; color:#444; margin-top:5px;'>{m['text'][:250]}...</p>
                </div>
                """, unsafe_allow_html=True)
else:
    st.error(f"File {DATA_FILE} not found.")
