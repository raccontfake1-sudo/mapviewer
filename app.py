import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# 1. إعدادات الصفحة الأساسية
st.set_page_config(
    page_title="Control Mapping Viewer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# CSS STYLE - التنسيق الجمالي
# -------------------------
st.markdown("""
<style>
body {
    background-color: #f5f5f5;
}

.block-container {
    padding-top: 1.5rem;
    padding-left: 2rem;
    padding-right: 1.5rem;
}

[data-testid="stSidebar"] {
    min-width: 420px;
    max-width: 420px;
    background-color: #ffffff;
    border-right: 1px solid #ddd;
}

.main-title {
    font-size: 52px;
    font-weight: 800;
    color: #2f2f2f;
    margin-bottom: 5px;
}

.subtitle {
    font-size: 20px;
    color: #4b5563;
    margin-top: -5px;
    margin-bottom: 25px;
}

.sidebar-title {
    font-size: 22px;
    font-weight: 800;
    color: #1f2937;
    margin-bottom: 15px;
}

.mapping-card {
    border: 2px solid #75b843;
    border-radius: 8px;
    background-color: #f1faec;
    padding: 16px;
    margin-bottom: 16px;
    transition: transform 0.2s;
}

.mapping-title {
    font-size: 19px;
    font-weight: 800;
    color: #1476d4;
}

.rank-pill {
    background-color: #1476d4;
    color: white;
    border-radius: 20px;
    padding: 4px 12px;
    font-weight: 700;
    margin-right: 8px;
    font-size: 14px;
}

.mapping-text {
    color: #444;
    font-size: 14.5px;
    line-height: 1.6;
    margin-top: 10px;
}

.graph-box {
    border: 1px solid #e0e0e0;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* تنسيق أزرار القائمة الجانبية */
[data-testid="stSidebar"] div.stButton > button {
    width: 100%;
    text-align: left;
    justify-content: flex-start;
    align-items: flex-start;
    white-space: normal;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #eee;
    background-color: #fff;
    margin-bottom: 10px;
    line-height: 1.4;
}

[data-testid="stSidebar"] div.stButton > button:hover {
    border: 1px solid #1476d4;
    background-color: #f0f7ff;
}

.selected-control-card button {
    background-color: #e8f4ff !important;
    border: 2px solid #1476d4 !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# HELPERS - الدوال المساعدة
# -------------------------
def short_text(text, limit=120):
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "..."

def get_mapping_columns(i):
    """إرجاع أسماء الأعمدة ديناميكياً بناءً على الرقم i"""
    if i == 1:
        return {
            "mapping": "NIST mapping",
            "text": "Text",
            "final": "Final Score",
            "confidence": "Confidence match"
        }
    return {
        "mapping": f"NIST mapping {i}",
        "text": f"Text {i}",
        "final": f"Final Score {i}",
        "confidence": f"Confidence match {i}"
    }

def extract_mappings(row, df, top_k):
    """استخراج وترتيب الموابق من الأقرب (الأعلى سكور) إلى الأبعد"""
    results = []
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        if cols["mapping"] not in df.columns or pd.isna(row.get(cols["mapping"])):
            continue

        # معالجة السكور لضمان أنه قيمة رقمية (Float)
        try:
            val = str(row.get(cols["final"], 0)).replace('%', '')
            final_score = float(val) if val else 0.0
            # تصحيح إذا كانت النسبة مئوية (مثلاً 91 بدلاً من 0.91)
            if final_score > 1.0:
                final_score = final_score / 100.0
        except:
            final_score = 0.0

        results.append({
            "original_rank": i,
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "final": final_score,
            "confidence": str(row.get(cols["confidence"], "N/A"))
        })

    # الترتيب التنازلي بناءً على السكور (الأقرب أولاً)
    results = sorted(results, key=lambda x: x["final"], reverse=True)
    return results[:top_k]

def create_graph(selected_control, source_text, mappings):
    """إنشاء الرسم البياني الشبكي"""
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#333")
    
    # إعدادات الفيزياء لجعل الرسم متمركزاً وجميلاً
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {"gravitationalConstant": -50, "centralGravity": 0.01, "springLength": 100},
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based"
      },
      "nodes": {"font": {"size": 16}},
      "edges": {"smooth": {"type": "continuous"}}
    }
    """)

    # إضافة العقدة المركزية (الضابط المختار)
    net.add_node(selected_control, label=selected_control, title=html.escape(source_text), 
                 color="#1687d9", size=40, shape="dot")

    # إضافة الموابق المرتبة
    for idx, item in enumerate(mappings):
        score_val = item["final"] * 100
        # لون العقدة بناءً على قوة القرب (أخضر للأقرب جداً)
        node_color = "#328a36" if item["final"] >= 0.85 else "#6366f1"
        
        net.add_node(item["mapping"], label=item["mapping"], title=html.escape(item["text"]), 
                     color=node_color, size=25)
        
        # ربط العقدة المركزية بالمطابقة مع إظهار النسبة على الخط
        net.add_edge(selected_control, item["mapping"], label=f"{score_val:.0f}%", 
                     value=item["final"] * 5, color="#d1d5db")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, "r", encoding="utf-8") as f:
            return f.read()

# -------------------------
# DATA LOADING - تحميل البيانات
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

@st.cache_data
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return None

df = load_data()

if df is None:
    st.error(f"⚠️ الملف '{DATA_FILE}' غير موجود في المستودع.")
    st.stop()

# تنظيف أسماء الأعمدة (في حال وجود مسافات)
df.columns = [c.strip() for c in df.columns]
control_col = "ECC id control"
source_col = "Source Text"

# -------------------------
# SIDEBAR - القائمة الجانبية
# -------------------------
st.sidebar.markdown('<div class="sidebar-title">ECC Controls</div>', unsafe_allow_html=True)

# البحث
search_query = st.sidebar.text_input("🔍 Search by ID...", placeholder="e.g. 1.1")
filtered_df = df.copy()
if search_query:
    filtered_df = df[df[control_col].astype(str).str.contains(search_query, case=False)]

# إدارة الحالة (State) للتحكم المختار
if "selected_id" not in st.session_state:
    st.session_state.selected_id = str(df[control_col].iloc[0])

# عرض الأزرار في حاوية قابلة للتمرير
scroll_container = st.sidebar.container(height=650)
with scroll_container:
    for idx, row in filtered_df.iterrows():
        cid = str(row[control_col])
        txt_preview = short_text(row[source_col])
        
        is_selected = (cid == st.session_state.selected_id)
        if is_selected:
            st.markdown('<div class="selected-control-card">', unsafe_allow_html=True)
            
        if st.button(f"📌 {cid}\n{txt_preview}", key=f"btn_{cid}_{idx}"):
            st.session_state.selected_id = cid
            st.rerun()
            
        if is_selected:
            st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# MAIN CONTENT - العرض الرئيسي
# -------------------------
# استخراج بيانات الصف المختار
selected_row = df[df[control_col].astype(str) == st.session_state.selected_id].iloc[0]
mappings = extract_mappings(selected_row, df, top_k=10)

st.markdown('<div class="main-title">Control Mapping Viewer</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Showing results for Control: <b>{st.session_state.selected_id}</b></div>', unsafe_allow_html=True)

col_graph, col_list = st.columns([3, 2])

with col_graph:
    st.markdown("### 🕸️ Visual Mapping")
    st.markdown('<div class="graph-box">', unsafe_allow_html=True)
    html_data = create_graph(st.session_state.selected_id, str(selected_row[source_col]), mappings)
    components.html(html_data, height=620)
    st.markdown('</div>', unsafe_allow_html=True)

with col_list:
    st.markdown("### 🏆 Top Recommendations (Sorted)")
    results_container = st.container(height=620)
    with results_container:
        if not mappings:
            st.info("No mappings found for this control.")
        else:
            for idx, item in enumerate(mappings):
                # عرض السكور بالنسبة المئوية
                display_score = f"{item['final']*100:.1f}%"
                
                st.markdown(f"""
                <div class="mapping-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="mapping-title">#{idx+1} | {item['mapping']}</span>
                        <span class="rank-pill">Score: {display_score}</span>
                    </div>
                    <div class="mapping-text">{item['text']}</div>
                    <div style="margin-top: 8px; font-size: 12px; color: #666; font-style: italic;">
                        Confidence Level: {item['confidence']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# تذييل الصفحة (Footer)
st.markdown("---")
st.caption(f"Yemen Mobile Dev Workflow | Data source: {DATA_FILE}")
