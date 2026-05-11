import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import os
import re

# 1. إعداد الصفحة
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# 2. تصميم الواجهة (CSS) - تم تبسيطه لضمان التوافق
st.markdown("""
<style>
    .main-title { font-size: 28px; font-weight: bold; color: #1e1e1e; }
    /* صندوق التفسيرات */
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

# 3. دالة تنظيف النصوص من أي وسوم زائدة قد تكون في ملف الـ CSV
def clean_text(text):
    if pd.isna(text): return "N/A"
    # مسح أي وسوم HTML موجودة مسبقاً في النص لتجنب التداخل
    text = re.sub('<[^<]+?>', '', str(text))
    return text.strip()

# 4. جلب البيانات من الأعمدة
def get_mapping_data(row, df):
    results = []
    for i in range(1, 11):
        suffix = "" if i == 1 else f" {i}"
        m_col = f"NIST mapping{suffix}"
        
        if m_col in df.columns and pd.notna(row.get(m_col)):
            results.append({
                "rank": i,
                "mapping": str(row.get(m_col)),
                "commonality": clean_text(row.get(f"Commonality{suffix}")),
                "justification": clean_text(row.get(f"Justification{suffix}")),
                "differences": clean_text(row.get(f"Differences{suffix}"))
            })
    return results

# 5. بناء الرسم البياني
def build_graph(center_id, mappings):
    net = Network(height="500px", width="100%", bgcolor="#ffffff", directed=False)
    net.add_node(center_id, label=center_id, color="#1687d9", size=35, font={'color': 'white'})
    for m in mappings:
        net.add_node(m["mapping"], label=m["mapping"], color="#328a36", size=25, font={'color': 'white'})
        net.add_edge(center_id, m["mapping"], label=f"#{m['rank']}", color="#dcd2d2", font={'size': 12, 'color': '#1476d4'})
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# 6. تشغيل التطبيق
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    
    # القائمة الجانبية
    st.sidebar.header("Controls Selection")
    all_ids = df["ECC id control"].unique()
    selected_id = st.sidebar.selectbox("Choose ID:", all_ids)
    
    # جلب البيانات
    row_data = df[df["ECC id control"] == selected_id].iloc[0]
    mappings = get_mapping_data(row_data, df)

    st.markdown(f'<div class="main-title">Control Mapping Viewer: {selected_id}</div>', unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.write("### Network Visualization")
        html_data = build_graph(str(selected_id), mappings)
        components.html(html_data, height=550)

    with col_right:
        st.write("### 🤖 AI Explanations")
        for m in mappings:
            with st.expander(f"#{m['rank']} - {m['mapping']}", expanded=(m['rank'] == 1)):
                # هنا السر: نستخدم f-string مع HTML داخل markdown
                # مع تفعيل unsafe_allow_html=True
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
    st.error("File not found.")
