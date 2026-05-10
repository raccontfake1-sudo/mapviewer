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
body {
    background-color: #f5f5f5;
}

.block-container {
    padding-top: 2rem;
    padding-left: 2rem;
    padding-right: 1rem;
}

[data-testid="stSidebar"] {
    min-width: 430px;
    max-width: 430px;
    background-color: #ffffff;
    border-right: 1px solid #ddd;
}

.main-title {
    font-size: 64px;
    font-weight: 800;
    color: #2f2f2f;
    margin-bottom: 0;
}

.subtitle {
    font-size: 22px;
    color: #111827;
    margin-top: -8px;
}

.sidebar-title {
    font-size: 22px;
    font-weight: 800;
    color: #1f2937;
    margin-bottom: 12px;
}

.mapping-card {
    border: 2px solid #75b843;
    border-radius: 6px;
    background-color: #f1faec;
    padding: 14px;
    margin-bottom: 14px;
}

.mapping-title {
    font-size: 20px;
    font-weight: 800;
    color: #1476d4;
}

.rank-pill {
    background-color: #1476d4;
    color: white;
    border-radius: 18px;
    padding: 5px 10px;
    font-weight: 700;
    margin-right: 10px;
}

.mapping-text {
    clear: both;
    color: #555;
    font-size: 15px;
    line-height: 1.5;
    margin-top: 12px;
}

.graph-box {
    border: 1px solid #d8d8d8;
    background-color: white;
    border-radius: 5px;
    padding: 0px;
}

/* Sidebar Buttons Styling */
[data-testid="stSidebar"] div.stButton > button {
    width: 100%;
    height: auto;
    min-height: 120px;
    text-align: left;
    justify-content: flex-start;
    align-items: flex-start;
    white-space: normal;
    padding: 14px;
    border-radius: 6px;
    border: 1px solid #e5e5e5;
    background-color: #ffffff;
    color: #444;
    margin-bottom: 8px;
}

[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #eaf6ff;
    border: 1px solid #1476d4;
    color: #1476d4;
}

.selected-control-card button {
    background-color: #dff0ff !important;
    border: 2px solid #1476d4 !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# HELPERS 
# -------------------------
def short_text(text, limit=150):
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "..."

def get_mapping_columns(i):
    if i == 1:
        return {
            "mapping": "NIST mapping",
            "text": "Text",
            "dense": "Dense",
            "sparse": "Sparse",
            "hybrid": "Hybrid",
            "ontology": "Ontology Score",
            "final": "Final Score",
            "confidence": "Confidence match"
        }
    return {
        "mapping": f"NIST mapping {i}",
        "text": f"Text {i}",
        "dense": f"Dense {i}",
        "sparse": f"Sparse {i}",
        "hybrid": f"Hybrid {i}",
        "ontology": f"Ontology Score {i}",
        "final": f"Final Score {i}",
        "confidence": f"Confidence match {i}"
    }

def extract_mappings(row, df, top_k):
    results = []
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        if cols["mapping"] not in df.columns:
            continue
        if pd.isna(row.get(cols["mapping"])):
            continue

        # تنظيف السكور وتحويله لرقم للترتيب الصحيح
        try:
            val = str(row.get(cols["final"], 0)).replace('%', '')
            final_score = float(val) if val else 0.0
            # إذا كان السكور بصيغة 0-100 وليس 0-1
            if final_score > 1:
                final_score = final_score / 100.0
        except:
            final_score = 0.0

        results.append({
            "rank": i,
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "dense": row.get(cols["dense"], 0),
            "sparse": row.get(cols["sparse"], 0),
            "hybrid": row.get(cols["hybrid"], 0),
            "ontology": row.get(cols["ontology"], ""),
            "final": final_score,
            "confidence": str(row.get(cols["confidence"], ""))
        })

    # الترتيب التنازلي: الأقرب (أعلى سكور) يظهر أولاً
    results = sorted(results, key=lambda x: x["final"], reverse=True)
    return results[:top_k]

def create_graph(selected_control, source_text, mappings):
    net = Network(height="580px", width="100%", bgcolor="#ffffff", directed=False)
    net.set_options("""
    {
      "nodes": {"borderWidth": 2, "font": {"size": 18, "color": "white"}},
      "edges": {"color": {"color": "#bdbdbd", "highlight": "#19a34a"}, "smooth": false},
      "physics": {
        "enabled": true,
        "repulsion": {"nodeDistance": 180, "centralGravity": 0.18},
        "stabilization": {"enabled": true, "iterations": 200}
      }
    }
    """)

    net.add_node(selected_control, label=selected_control, title=html.escape(source_text), 
                 color={"background": "#1687d9", "border": "#0b4f8a"}, 
                 font={"color": "#ffffff", "size": 50, "bold": True}, shape="circle", size=150)

    for item in mappings:
        score_percent = item["final"] * 100
        net.add_node(item["mapping"], label=item["mapping"], title=html.escape(item["text"]), 
                     color={"background": "#328a36", "border": "#1b1b1b"},
                     font={"color": "#ffffff", "size": 20, "bold": True}, shape="circle", size=30)

        edge_color = "#10b981" if item["final"] >= 0.7 else "#f59e0b"
        net.add_edge(selected_control, item["mapping"], label=f"{score_percent:.0f}%", 
                     value=max(score_percent / 25, 1), color={"color": "#dcd2d2", "highlight": edge_color})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, "r", encoding="utf-8") as f:
            return f.read()

# -------------------------
# DATA LOADING
# -------------------------
DATA_PATH = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    st.error(f"File '{DATA_PATH}' not found.")
    st.stop()

control_col = "ECC id control"
source_col = "Source Text"
controls_df = df[[control_col, source_col]].dropna().copy()
controls_df[control_col] = controls_df[control_col].astype(str)

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.markdown('<div class="sidebar-title">ECC Selection:</div>', unsafe_allow_html=True)
search = st.sidebar.text_input("", placeholder="Search ID (e.g., 1.1)...")
if search:
    controls_df = controls_df[controls_df[control_col].str.contains(search, case=False, na=False)]

if "selected_control" not in st.session_state:
    st.session_state.selected_control = controls_df[control_col].iloc[0]

control_box = st.sidebar.container(height=550, border=True)
with control_box:
    for i, r in controls_df.iterrows():
        cid = str(r[control_col])
        preview = short_text(r[source_col], 100)
        if cid == st.session_state.selected_control:
            st.markdown('<div class="selected-control-card">', unsafe_allow_html=True)
        if st.button(f"{cid}\n\n{preview}", key=f"btn_{cid}"):
            st.session_state.selected_control = cid
            st.rerun()
        if cid == st.session_state.selected_control:
            st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# MAIN UI
# -------------------------
tab_choice = st.sidebar.radio("", ["📊 Mappings", "📈 Analytics"], horizontal=True)

selected_id = st.session_state.selected_control
row = df[df[control_col].astype(str) == selected_id].iloc[0]
mappings = extract_mappings(row, df, top_k=10)

if tab_choice == "📊 Mappings":
    st.markdown('<div class="main-title">Control Mapping Viewer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">Viewing: <b>{selected_id}</b></div>', unsafe_allow_html=True)

    left, right = st.columns([3, 2])
    with left:
        st.markdown('<div class="graph-box">', unsafe_allow_html=True)
        graph_html = create_graph(selected_id, str(row[source_col]), mappings)
        components.html(graph_html, height=600)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with right:
        st.markdown("### Top Recommendations")
        card_container = st.container(height=600)
        with card_container:
            for item in mappings:
                st.markdown(f"""
                <div class="mapping-card">
                    <span class="rank-pill">#{item['rank']}</span>
                    <span class="mapping-title">{item['mapping']} - {item['final']*100:.0f}%</span>
                    <div class="mapping-text">{item['text']}</div>
                    <div style="font-size: 12px; color: #1476d4; margin-top:5px;">Confidence: {item['confidence']}</div>
                </div>
                """, unsafe_allow_html=True)

elif tab_choice == "📈 Analytics":
    st.title("Framework Analytics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Controls", len(df))
    col2.metric("Mapped Controls", df['NIST mapping'].notna().sum())
    col3.metric("Coverage", f"{(df['NIST mapping'].notna().sum()/len(df))*100:.1f}%")
    st.bar_chart(df['ECC id control'].value_counts().head(10))
