import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# 1. إعدادات الصفحة
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# -------------------------
# CSS STYLE - تحسين المظهر
# -------------------------
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    .mapping-card { 
        border: 2px solid #75b843; 
        border-radius: 8px; 
        background-color: #f1faec; 
        padding: 15px; 
        margin-bottom: 10px; 
    }
    .rank-pill { 
        background-color: #1476d4; 
        color: white; 
        border-radius: 15px; 
        padding: 2px 10px; 
        font-weight: bold; 
    }
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
    # ترتيب من الأقرب (الأعلى سكور) للأبعد
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

def create_graph(selected_id, source_text, mappings):
    net = Network(height="700px", width="100%", bgcolor="#ffffff", font_color="#333")
    
    # إعدادات الفيزياء لجعل التوزيع دائرياً ومنظماً
    net.set_options("""
    {
      "nodes": { "font": { "size": 18, "face": "arial" }, "borderWidth": 2 },
      "edges": { 
        "font": { "size": 16, "align": "middle", "color": "#1476d4", "strokeWidth": 4, "strokeColor": "#ffffff" },
        "color": { "color": "#d3dbe3" },
        "smooth": { "type": "continuous" }
      },
      "physics": {
        "forceAtlas2Based": { "gravitationalConstant": -120, "springLength": 180 },
        "solver": "forceAtlas2Based"
      }
    }
    """)

    # العقدة المركزية
    net.add_node(selected_id, label=selected_id, title=html.escape(source_text), 
                 color="#1687d9", size=45, shape="circle", font={'color':'white', 'bold':True})

    for idx, item in enumerate(mappings):
        rank_label = f"#{idx + 1}" # الترقيم من #1 إلى #10
        
        # التحكم في سمك السهم بناءً على الترتيب (الأول أسمك)
        edge_thickness = 8 - (idx * 0.7) 
        
        # العقدة الفرعية
        net.add_node(item["mapping"], label=item["mapping"], title=html.escape(item["text"]), 
                     color="#328a36", size=30, shape="circle", font={'color':'white'})
        
        # ربط السهم مع الترقيم والسمك المطلوب
        net.add_edge(selected_id, item["mapping"], label=rank_label, width=edge_thickness)

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
    
    if "selected_id" not in st.session_state: 
        st.session_state.selected_id = str(df["ECC id control"].iloc[0])

    st.title("Control Mapping Viewer")
    
    # اختيار التحكم من القائمة الجانبية
    st.sidebar.title("ECC Controls List")
    search = st.sidebar.text_input("🔍 Search ID...", "")
    filtered_df = df[df["ECC id control"].astype(str).str.contains(search)] if search else df
    
    with st.sidebar.container(height=600):
        for cid in filtered_df["ECC id control"].unique():
            if st.button(f"📌 {cid}", key=f"btn_{cid}"):
                st.session_state.selected_id = str(cid)
                st.rerun()

    # معالجة البيانات للعنصر المختار
    row = df[df["ECC id control"].astype(str) == st.session_state.selected_id].iloc[0]
    mappings = extract_mappings(row, df)

    col_graph, col_list = st.columns([7, 3])

    with col_graph:
        st.subheader(f"Visual Mapping for: {st.session_state.selected_id}")
        graph_html = create_graph(st.session_state.selected_id, str(row["Source Text"]), mappings)
        components.html(graph_html, height=750)

    with col_list:
        st.subheader("Recommendations")
        with st.container(height=720):
            for idx, m in enumerate(mappings):
                st.markdown(f"""
                <div class="mapping-card">
                    <span class="rank-pill">#{idx+1}</span> <b>{m['mapping']}</b>
                    <p style='font-size:13px; color:#444; margin-top:5px;'>{m['text'][:200]}...</p>
                </div>
                """, unsafe_allow_html=True)
else:
    st.error("Data file not found.")
