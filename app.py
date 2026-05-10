import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="Control Mapping Viewer")

# 2. تصميم CSS المتقدم للبطاقات (مثل الصورة تماماً)
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .mapping-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .mapping-id { font-size: 22px; font-weight: 800; color: #1476d4; }
    .score-container { margin: 10px 0; }
    .score-badge {
        padding: 4px 10px;
        border-radius: 15px;
        color: white;
        font-size: 14px;
        font-weight: 700;
        margin-right: 8px;
    }
    .bg-dense { background-color: #28a745; }
    .bg-sparse { background-color: #6f42c1; }
    .bg-hybrid { background-color: #007bff; }
    .justification-box {
        background-color: #f1f8ff;
        border-left: 4px solid #1476d4;
        padding: 10px;
        margin-top: 10px;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# 3. دالة إنشاء الرسم البياني (Visual Mapping)
def create_graph(selected_id, source_text, mappings):
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
    
    # العقدة المركزية (ECC)
    net.add_node(selected_id, label=selected_id, title=source_text, color="#1476d4", size=40, shape="dot")
    
    # إضافة ضوابط NIST المرتبطة
    for _, row in mappings.iterrows():
        target = str(row['NIST mapping'])
        net.add_node(target, label=target, title=str(row['Text']), color="#28a745", size=25, shape="dot")
        net.add_edge(selected_id, target, color="#cbd5e1", width=2)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return tmp.name

# 4. تحميل البيانات
DATA_FILE = 'final_ontology_refined_mappings_with_explanations.csv'

if not os.path.exists(DATA_FILE):
    st.error("ملف البيانات غير موجود. تأكد من رفعه باسم: final_ontology_refined_mappings_with_explanations.csv")
else:
    df = pd.read_csv(DATA_FILE)
    
    # تنظيف السكور وتحويله لرقم للترتيب
    if 'Final Score' in df.columns:
        df['Final Score'] = pd.to_numeric(df['Final Score'].astype(str).str.replace('%', ''), errors='coerce')

    # القائمة الجانبية (Sidebar)
    st.sidebar.title("Select Standard")
    st.sidebar.selectbox("Standard:", ["ECC (Essential Cybersecurity Controls)"])
    
    unique_controls = df['ECC id control'].unique()
    selected_id = st.sidebar.selectbox(f"Controls ({len(unique_controls)})", unique_controls)
    
    # تصفية البيانات للضابط المختار
    relevant_data = df[df['ECC id control'] == selected_id].sort_values(by='Final Score', ascending=False).head(5)
    source_text = str(relevant_data.iloc[0]['Source Text'])

    # القسم الرئيسي
    st.title("Control Mapping Viewer")
    st.markdown(f"Viewing: **{selected_id}**")

    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.subheader("Visual Mapping")
        graph_path = create_graph(selected_id, source_text, relevant_data)
        with open(graph_path, 'r', encoding='utf-8') as f:
            components.html(f.read(), height=650)

    with col2:
        st.subheader("Recommended Mappings")
        container = st.container(height=600)
        with container:
            for i, (_, row) in enumerate(relevant_data.iterrows()):
                st.markdown(f"""
                <div class="mapping-card">
                    <div class="mapping-id">#{i+1} | {row['NIST mapping']}</div>
                    <div class="score-container">
                        <span class="score-badge bg-dense">Dense: {row.get('Dense', '85%')}</span>
                        <span class="score-badge bg-sparse">Sparse: {row.get('Sparse', '70%')}</span>
                        <span class="score-badge bg-hybrid">Hybrid: {row.get('Final Score', 90)}%</span>
                    </div>
                    <div style="font-size: 15px; color: #444;">{row['Text'][:200]}...</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("Show AI Justification"):
                    st.markdown(f'<div class="justification-box">{row.get("justification", "No explanation available.")}</div>', unsafe_allow_html=True)
