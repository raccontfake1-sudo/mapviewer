import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="ECC-NIST Mapping Tool")

# 2. تصميم CSS المتقدم (للبطاقات والخطوط)
st.markdown("""
<style>
    .main { background-color: #f4f7f9; }
    .mapping-card {
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .mapping-title { font-size: 20px; font-weight: 800; color: #1476d4; }
    .score-badge {
        padding: 4px 12px;
        border-radius: 20px;
        color: white;
        font-size: 13px;
        font-weight: 700;
        margin-right: 5px;
    }
    .bg-green { background-color: #28a745; }
    .bg-purple { background-color: #6f42c1; }
    .bg-blue { background-color: #007bff; }
    .justification-box {
        background-color: #f8f9fa;
        border-right: 4px solid #1476d4;
        padding: 12px;
        margin-top: 10px;
        font-size: 14px;
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# 3. دالة إنشاء الرسم البياني (Visual Mapping)
def create_graph(selected_id, source_text, mappings):
    net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black")
    # العقدة المركزية
    net.add_node(selected_id, label=selected_id, title=source_text, color="#1476d4", size=40)
    # العقد المرتبطة
    for _, row in mappings.iterrows():
        target = str(row['NIST mapping'])
        net.add_node(target, label=target, title=str(row['Text']), color="#28a745", size=25)
        net.add_edge(selected_id, target, color="#cbd5e1")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return tmp.name

# 4. تحميل ومعالجة البيانات
DATA_FILE = 'final_ontology_refined_mappings_with_explanations.csv'

if not os.path.exists(DATA_FILE):
    st.error("ملف البيانات مفقود! تأكد من رفعه للمستودع.")
else:
    df = pd.read_csv(DATA_FILE)
    if 'Final Score' in df.columns:
        df['Final Score'] = pd.to_numeric(df['Final Score'].astype(str).str.replace('%', ''), errors='coerce')

    # القائمة الجانبية
    st.sidebar.title("Standard Selection")
    unique_controls = df['ECC id control'].unique()
    selected_id = st.sidebar.selectbox(f"Controls ({len(unique_controls)})", unique_controls)
    
    # فلترة البيانات
    relevant_data = df[df['ECC id control'] == selected_id].sort_values(by='Final Score', ascending=False).head(5)
    source_text = str(relevant_data.iloc[0]['Source Text'])

    # العرض الرئيسي
    st.title("Control Mapping Viewer")
    
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("Visual Mapping (Interactive)")
        graph_path = create_graph(selected_id, source_text, relevant_data)
        with open(graph_path, 'r', encoding='utf-8') as f:
            components.html(f.read(), height=550)

    with col2:
        st.subheader("Recommended Mappings")
        for i, (_, row) in enumerate(relevant_data.iterrows()):
            st.markdown(f"""
            <div class="mapping-card">
                <div class="mapping-title">#{i+1} | {row['NIST mapping']}</div>
                <div style="margin: 10px 0;">
                    <span class="score-badge bg-green">E: {row.get('Dense', '85%')}</span>
                    <span class="score-badge bg-purple">O: {row.get('Sparse', '70%')}</span>
                    <span class="score-badge bg-blue">J: {row.get('Final Score', 90)}%</span>
                </div>
                <div style="font-size: 14px; color: #555;">{row['Text'][:150]}...</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View AI Explanation"):
                st.markdown(f'<div class="justification-box">{row.get("justification", "لا يوجد تبرير متاح حالياً.")}</div>', unsafe_allow_html=True)
