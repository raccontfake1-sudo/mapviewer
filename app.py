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
    .main-title { font-size: 32px; font-weight: 800; color: #2f2f2f; margin-bottom: 10px; }
    .subtitle { font-size: 16px; color: #666; margin-bottom: 20px; }
    
    /* تنسيق صندوق التفسيرات الاحترافي الداكن */
    .explanation-box {
        background-color: #1e1e1e; 
        padding: 20px; 
        border-radius: 12px; 
        color: #dcdcdc; 
        border-left: 5px solid #1476d4;
        margin-bottom: 10px;
        font-family: 'Segoe UI', sans-serif;
    }
    .exp-label { color: #58a6ff; font-weight: bold; font-size: 15px; margin-top: 12px; display: block; }
    .exp-content { font-size: 14px; line-height: 1.6; color: #f0f0f0; margin-bottom: 5px; }
    
    /* تحسين شكل القائمة الجانبية */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #ddd; }
    div.stButton > button {
        width: 100%; text-align: left; padding: 12px;
        border-radius: 8px; border: 1px solid #eee; background-color: white;
        margin-bottom: 5px; transition: 0.3s;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# 2. وظائف معالجة البيانات
# -------------------------
def clean_html_tags(text):
    """تنظيف النصوص من وسوم HTML إذا وجدت بداخل البيانات"""
    if pd.isna(text): return "N/A"
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', str(text))

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
        
        # تنظيف البيانات من أي وسوم HTML زائدة موجودة في ملف الـ CSV نفسه
        results.append({
            "rank": i,
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "commonality": clean_html_tags(row.get(cols["commonality"])),
            "justification": clean_html_tags(row.get(cols["justification"])),
            "differences": clean_html_tags(row.get(cols["differences"]))
        })
    return results

# -------------------------
# 3. بناء الرسم البياني
# -------------------------
def create_styled_graph(selected_id, source_text, mappings):
    net = Network(height="550px", width="100%", bgcolor="#ffffff", directed=False)
    net.add_node(selected_id, label=selected_id, color="#1687d9", size=40, font={'color': 'white', 'bold': True})
    for item in mappings:
        net.add_node(item["mapping"], label=item["mapping"], color="#328a36", size=25, font={'color': 'white'})
        net.add_edge(selected_id, item["mapping"], label=f"#{item['rank']}", width=2, color="#dcd2d2", 
                     font={'size': 14, 'color': '#1476d4', 'strokeWidth': 2, 'strokeColor': '#ffffff'})
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# -------------------------
# 4. الواجهة الرئيسية
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    st.sidebar.title("Controls")
    
    if "selected_id" not in st.session_state:
        st.session_state.selected_id = str(df["ECC id control"].iloc[0])

    # قائمة البحث والاختيار
    search = st.sidebar.text_input("Search ID:", placeholder="e.g. 1.1")
    f_df = df[df["ECC id control"].astype(str).str.contains(search)] if search else df
    
    for _, r in f_df.head(20).iterrows(): # عرض أول 20 لسرعة التحميل
        if st.sidebar.button(f"ID: {r['ECC id control']}", key=f"b_{r['ECC id control']}"):
            st.session_state.selected_id = str(r["ECC id control"])

    current_id = st.session_state.selected_id
    row_data = df[df["ECC id control"].astype(str) == current_id].iloc[0]
    mappings = extract_mappings(row_data, df)

    st.markdown(f'<div class="main-title">Control Mapping Viewer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">Viewing: <b>{current_id}</b></div>', unsafe_allow_html=True)

    col_graph, col_info = st.columns([1.3, 1])

    with col_graph:
        graph_html = create_styled_graph(current_id, str(row_data["Source Text"]), mappings)
        components.html(graph_html, height=580)

    with col_info:
        st.write("### 🤖 AI Explanations")
        info_container = st.container(height=550)
        with info_container:
            for m in mappings:
                # استخدام expander مع عرض البيانات النظيفة مباشرة
                with st.expander(f"**#{m['rank']} - {m['mapping']}**", expanded=(m['rank'] == 1)):
                    st.markdown(f"""
                    <div class="explanation-box">
                        <div class="exp-label">Commonality:</div>
                        <div class="exp-content">{m['commonality']}</div>
                        
                        <div class="exp-label">Justification:</div>
                        <div class="exp-content">{m['justification']}</div>
                        
                        <div class="exp-label">Differences:</div>
                        <div class="exp-content">{m['differences']}</div>
                    </div>
                    """, unsafe_allow_html=True)
else:
    st.error("CSV file not found.")
