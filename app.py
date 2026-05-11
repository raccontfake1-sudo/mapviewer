import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os
import re # أضفنا مكتبة re لتنظيف النص

# إعداد الصفحة
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# -------------------------
# دالة تنظيف النص من أكواد HTML الزائدة (الحل الجذري)
# -------------------------
def clean_html_from_text(raw_text):
    if pd.isna(raw_text): return "N/A"
    # إزالة أي وسوم HTML قد تكون موجودة داخل خلايا الـ CSV
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', str(raw_text))
    # تحويل الرموز المشفرة مثل &amp; إلى رموزها الطبيعية
    return html.unescape(cleantext).strip()

# -------------------------
# CSS STYLE - تم تعديله لضمان نظافة العرض
# -------------------------
st.markdown("""
<style>
    .explanation-box {
        background-color: #1a1c24;
        color: #e0e0e0;
        border: 1px solid #3d3f4b;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .exp-label { color: #58a6ff; font-weight: bold; margin-top: 10px; display: block; font-size: 15px; }
    .exp-text { margin-bottom: 15px; line-height: 1.6; color: #ffffff; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# وظائف معالجة البيانات
# -------------------------
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

def extract_mappings(row, df, top_k=10):
    results = []
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        if cols["mapping"] not in df.columns or pd.isna(row.get(cols["mapping"])): continue
        
        # تنظيف البيانات مباشرة عند الاستخراج (استخدام دالة التنظيف هنا)
        results.append({
            "mapping": str(row.get(cols["mapping"], "")),
            "commonality": clean_html_from_text(row.get(cols["commonality"])),
            "justification": clean_html_from_text(row.get(cols["justification"])),
            "differences": clean_html_from_text(row.get(cols["differences"]))
        })
    return results[:top_k]

def create_graph(selected_id, mappings):
    net = Network(height="550px", width="100%", bgcolor="#ffffff", directed=False)
    net.add_node(selected_id, label=" ", color="#1687d9", size=45, shape="circle")
    for idx, item in enumerate(mappings):
        net.add_node(item["mapping"], label=item["mapping"], color="#328a36", size=30, font={'color':'white'})
        net.add_edge(selected_id, item["mapping"], label=f"#{idx+1}", width=2, color="#d3dbe3")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# -------------------------
# الواجهة الرئيسية
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    st.sidebar.title("Controls List")
    selected_id = st.sidebar.selectbox("Select Control ID:", df["ECC id control"].unique())
    
    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    mappings = extract_mappings(row, df)

    st.title(f"Mapping Viewer: {selected_id}")

    col_graph, col_exp = st.columns([1.2, 1])

    with col_graph:
        graph_html = create_graph(str(selected_id), mappings)
        components.html(graph_html, height=600)

    with col_exp:
        st.markdown("### 🤖 AI Explanations")
        # استخدام حاوية التمرير المدمجة في Streamlit لترتيب العرض
        for idx, m in enumerate(mappings):
            with st.expander(f"#{idx+1} - {m['mapping']}", expanded=(idx == 0)):
                st.markdown(f"""
                <div class="explanation-box">
                    <span class="exp-label">Commonality:</span>
                    <div class="exp-text">{m['commonality']}</div>
                    
                    <span class="exp-label">Justification:</span>
                    <div class="exp-text">{m['justification']}</div>
                    
                    <span class="exp-label">Differences:</span>
                    <div class="exp-text">{m['differences']}</div>
                </div>
                """, unsafe_allow_html=True)
else:
    st.error("Data file not found.")
