import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import os
import re

# 1. إعداد الصفحة والتصميم
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

st.markdown("""
<style>
    .main-title { font-size: 28px; font-weight: bold; color: #1e1e1e; }
    .exp-box {
        background-color: #1e1e1e; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #1476d4;
        margin: 10px 0px;
    }
    .label { color: #58a6ff; font-weight: bold; font-size: 14px; margin-bottom: 4px; }
    .content { color: #ffffff; font-size: 13.5px; line-height: 1.5; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# 2. دالة تنظيف البيانات (الحل الجذري لمشكلة ظهور الأكواد)
def sanitize_data(text):
    if pd.isna(text): return "N/A"
    # تحويل النص إلى سلسلة نصية
    text = str(text)
    # إزالة أي وسوم HTML مثل <div> <span> <p> وغيرها
    clean = re.compile('<.*?>')
    cleaned_text = re.sub(clean, '', text)
    # فك ترميز أي رموز خاصة مثل &amp; أو &quot;
    import html
    return html.unescape(cleaned_text).strip()

# 3. معالجة بيانات الأعمدة
def get_clean_mappings(row, df):
    results = []
    for i in range(1, 11):
        suffix = "" if i == 1 else f" {i}"
        m_col = f"NIST mapping{suffix}"
        
        if m_col in df.columns and pd.notna(row.get(m_col)):
            results.append({
                "rank": i,
                "mapping": str(row.get(m_col)),
                # تنظيف كل حقل بيانات بشكل منفصل
                "commonality": sanitize_data(row.get(f"Commonality{suffix}")),
                "justification": sanitize_data(row.get(f"Justification{suffix}")),
                "differences": sanitize_data(row.get(f"Differences{suffix}"))
            })
    return results

# 4. بناء الرسم البياني
def build_graph(center_id, mappings):
    net = Network(height="500px", width="100%", bgcolor="#ffffff", directed=False)
    net.add_node(center_id, label=center_id, color="#1687d9", size=35, font={'color': 'white'})
    for m in mappings:
        net.add_node(m["mapping"], label=m["mapping"], color="#328a36", size=25, font={'color': 'white'})
        net.add_edge(center_id, m["mapping"], label=f"#{m['rank']}", color="#dcd2d2", font={'size': 12, 'color': '#1476d4'})
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# 5. تشغيل التطبيق الرئيسي
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    
    st.sidebar.header("Controls Navigation")
    selected_id = st.sidebar.selectbox("Select Control ID:", df["ECC id control"].unique())
    
    row_data = df[df["ECC id control"] == selected_id].iloc[0]
    mappings = get_clean_mappings(row_data, df)

    st.markdown(f'<div class="main-title">Control Mapping: {selected_id}</div>', unsafe_allow_html=True)
    
    col_vis, col_exp = st.columns([1.2, 1])

    with col_vis:
        st.write("### Network Visualization")
        graph_html = build_graph(str(selected_id), mappings)
        components.html(graph_html, height=550)

    with col_exp:
        st.write("### 🤖 AI Explanations")
        for m in mappings:
            with st.expander(f"#{m['rank']} - {m['mapping']}", expanded=(m['rank'] == 1)):
                # العرض باستخدام Markdown نظيف تماماً
                st.markdown(f"""
                <div class="exp-box">
                    <div class="label">Commonality:</div>
                    <div class="content">{m['commonality']}</div>
                    
                    <div class="label">Justification:</div>
                    <div class="content">{m['justification']}</div>
                    
                    <div class="label">Differences:</div>
                    <div class="content">{m['differences']}</div>
                </div>
                """, unsafe_allow_html=True)
else:
    st.error("CSV file not found in the repository.")
