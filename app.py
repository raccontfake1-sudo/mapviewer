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
# CSS STYLE - التنسيق الجمالي
# -------------------------
st.markdown("""
<style>
    body { background-color: #f5f5f5; }
    [data-testid="stSidebar"] { min-width: 400px; max-width: 400px; }
    .mapping-card { border: 2px solid #75b843; border-radius: 8px; background-color: #f1faec; padding: 15px; margin-bottom: 10px; }
    .rank-pill { background-color: #1476d4; color: white; border-radius: 15px; padding: 2px 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# HELPERS - الدوال المساعدة
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
    # الترتيب من الأقرب (الأعلى سكور) للأبعد
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

def create_graph(selected_id, source_text, mappings):
    net = Network(height="600px", width="100%", bgcolor="#ffffff")
    
    # إعدادات النصوص على الأسهم لتشبه الصورة
    net.set_options("""
    {
      "edges": {
        "font": { "size": 12, "align": "middle", "color": "#2eb086", "strokeWidth": 0 },
        "color": { "color": "#d3d3d3" },
        "width": 2
      },
      "nodes": { "font": { "size": 16, "face": "arial" } },
      "physics": { "forceAtlas2Based": { "gravitationalConstant": -100, "springLength": 150 }, "solver": "forceAtlas2Based" }
    }
    """)

    # العقدة المركزية
    net.add_node(selected_id, label=selected_id, title=html.escape(source_text), color="#1687d9", size=40, shape="circle", font={'color':'white', 'bold':True})

    for item in mappings:
        score_val = int(item["final"] * 100)
        # تحديد النوع بناءً على القوة (مثل الصورة)
        label_type = "PRIMARY SUBSET" if score_val >= 88 else "SECONDARY SUBSET"
        edge_label = f"{label_type}\n{score_val}%"
        
        # إضافة العقدة المحيطة
        net.add_node(item["mapping"], label=item["mapping"], title=html.escape(item["text"]), color="#328a36", size=25, shape="circle", font={'color':'white'})
        
        # إضافة السهم مع النص المكتوب عليه
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
    
    # اختيار المعيار (Sidebar)
    st.sidebar.title("ECC Controls")
    search = st.sidebar.text_input("Search ID...", "")
    filtered_df = df[df["ECC id control"].astype(str).str.contains(search)] if search else df
    
    if "selected_id" not in st.session_state: st.session_state.selected_id = str(df["ECC id control"].iloc[0])
    
    with st.sidebar.container(height=500):
        for cid in filtered_df["ECC id control"].unique():
            if st.button(f"📌 {cid}", key=f"btn_{cid}"):
                st.session_state.selected_id = str(cid)

    # عرض النتائج
    row = df[df["ECC id control"].astype(str) == st.session_state.selected_id].iloc[0]
    mappings = extract_mappings(row, df)

    st.title("Control Mapping Viewer")
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader(f"Visual Mapping for: {st.session_state.selected_id}")
        graph_html = create_graph(st.session_state.selected_id, str(row["Source Text"]), mappings)
        components.html(graph_html, height=620)

    with col2:
        st.subheader("Top Recommendations")
        for idx, m in enumerate(mappings):
            st.markdown(f"""
            <div class="mapping-card">
                <span class="rank-pill">#{idx+1}</span> <b>{m['mapping']}</b> - {int(m['final']*100)}%
                <p style='font-size:13px; color:#555;'>{m['text'][:200]}...</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error(f"File {DATA_FILE} not found.")
