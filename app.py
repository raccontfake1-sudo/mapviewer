import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os 

# إعداد الصفحة
st.set_page_config(
    page_title="Control Mapping Viewer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# CSS STYLE (نفس تنسيقاتك الأصلية)
# -------------------------
st.markdown("""
<style>
    /* ... (نفس تنسيقات CSS التي أرسلتها في كودك) ... */
    .mapping-card { border: 2px solid #75b843; border-radius: 6px; background-color: #f1faec; padding: 14px; margin-bottom: 14px; }
    .mapping-title { font-size: 20px; font-weight: 800; color: #1476d4; }
    .rank-pill { background-color: #1476d4; color: white; border-radius: 18px; padding: 5px 10px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# HELPERS
# -------------------------
def short_text(text, limit=150):
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "..."

def get_mapping_columns(i):
    # دالة ذكية للتعامل مع تسميات الأعمدة المختلفة
    suffix = f" {i}" if i > 1 else ""
    return {
        "mapping": f"NIST mapping{suffix}",
        "text": f"Text{suffix}",
        "dense": f"Dense{suffix}",
        "sparse": f"Sparse{suffix}",
        "hybrid": f"Hybrid{suffix}",
        "ontology": f"Ontology score{suffix}",
        "final": f"Final Score{suffix}",
        "confidence": f"Confidence match{suffix}",
        "commonality": f"Commonality{suffix}",
        "justification": f"Justification{suffix}",
        "differences": f"Differences{suffix}"
    }

def extract_mappings(row, df, top_k):
    results = []
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        if cols["mapping"] not in df.columns: continue
        if pd.isna(row.get(cols["mapping"])): continue

        # جلب القيم مع التأكد من تحويل السكور لرقم للترتيب
        final_val = str(row.get(cols["final"], "0")).replace('%', '')
        try:
            final_score = float(final_val)
        except:
            final_score = 0.0

        results.append({
            "rank": i,
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "final": final_score,
            "commonality": row.get(cols["commonality"], "N/A"),
            "justification": row.get(cols["justification"], "N/A"),
            "differences": row.get(cols["differences"], "N/A")
        })

    # الترتيب: الأقرب (الأعلى سكور) فالأبعد
    results = sorted(results, key=lambda x: x["final"], reverse=True)
    return results[:top_k]

# -------------------------
# LOAD DATA (البحث الذكي عن الملف)
# -------------------------
DATA_FILES = [
    "final_with_explanations.csv", # الملف الناتج من step6
    "data/final_with_explanations.csv",
    "final_ontology_refined_mappings_with_explanations.csv"
]

df = None
for f_path in DATA_FILES:
    if os.path.exists(f_path):
        df = pd.read_csv(f_path)
        break

if df is None:
    st.error("لم يتم العثور على ملف البيانات. تأكد من تشغيل step6 أو وجود ملف CSV.")
    st.stop()

# -------------------------
# MAIN INTERFACE
# -------------------------
control_col = "ECC id control"
source_col = "Source Text"

# شريط البحث الجانبي
st.sidebar.markdown("### Controls Search")
search = st.sidebar.text_input("", placeholder="Search ID (e.g. 1.1)")

filtered_df = df.copy()
if search:
    filtered_df = filtered_df[filtered_df[control_col].astype(str).str.contains(search)]

# اختيار الـ Control
if not filtered_df.empty:
    if "selected_control" not in st.session_state:
        st.session_state.selected_control = str(filtered_df[control_col].iloc[0])
    
    # قائمة الأزرار الجانبية
    control_box = st.sidebar.container(height=500)
    with control_box:
        for _, r in filtered_df.iterrows():
            cid = str(r[control_col])
            if st.button(f"{cid}: {short_text(r[source_col], 50)}", key=cid):
                st.session_state.selected_control = cid
                st.rerun()

    selected_control = st.session_state.selected_control
    row = df[df[control_col].astype(str) == selected_control].iloc[0]
    
    # استخراج وعرض النتائج
    st.markdown(f'<div class="main-title">Mapping Results</div>', unsafe_allow_html=True)
    st.markdown(f"#### ECC Control: {selected_control}")
    st.info(row[source_col])

    mappings = extract_mappings(row, df, 10)

    # عرض التفاصيل في كروت مرتبة
    for item in mappings:
        with st.expander(f"#{item['rank']} | {item['mapping']} - Score: {item['final']}%"):
            st.markdown(f"**Description:** {item['text']}")
            st.success(f"**Commonality:** {item['commonality']}")
            st.info(f"**Justification:** {item['justification']}")
            st.warning(f"**Differences:** {item['differences']}")

else:
    st.warning("لا توجد نتائج تطابق بحثك.")
