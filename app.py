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

# إضافة تنسيقات CSS لتحسين المظهر
st.markdown("""
<style>
    .mapping-card { border: 2px solid #75b843; border-radius: 6px; padding: 15px; margin-bottom: 10px; background-color: #f9fbf7; }
    .mapping-title { font-size: 20px; font-weight: 800; color: #1476d4; margin-bottom: 8px; }
    .rank-pill { background-color: #1476d4; color: white; border-radius: 20px; padding: 2px 12px; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# دالة لتنظيف النصوص الطويلة
def short_text(text, limit=150):
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "..."

# أسماء الأعمدة بناءً على الملف الجديد في مستودعك
def get_mapping_columns(i):
    suffix = f".{i}" if i > 1 else ""
    return {
        "mapping": f"NIST mapping{suffix}",
        "text": f"Text{suffix}",
        "final": f"Final Score{suffix}",
        "justification": f"Justification{suffix}",
        "differences": f"Differences{suffix}"
    }

def extract_mappings(row, df, top_k):
    results = []
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        if cols["mapping"] not in df.columns: continue
        if pd.isna(row.get(cols["mapping"])): continue
        
        # تحويل السكور لرقم
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
            "justification": str(row.get(cols["justification"], "N/A")),
            "differences": str(row.get(cols["differences"], "N/A"))
        })
    
    # ترتيب النتائج حسب السكور الأعلى
    results = sorted(results, key=lambda x: x["final"], reverse=True)
    return results[:top_k]

# تحميل البيانات - تأكد من مطابقة الاسم للموجود في GitHub
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if not os.path.exists(DATA_FILE):
    st.error(f"الملف {DATA_FILE} غير موجود في المستودع. تأكد من رفعه.")
else:
    df = pd.read_csv(DATA_FILE)
    
    st.title("🔗 Control Mapping Explorer (AI Enhanced)")
    
    # القائمة الجانبية للبحث
    st.sidebar.header("البحث والفلترة")
    control_col = "Control ID" if "Control ID" in df.columns else df.columns[0]
    source_col = "Control Text" if "Control Text" in df.columns else df.columns[1]
    
    search = st.sidebar.selectbox("اختر رقم الضابط (Control ID):", df[control_col].unique())
    top_k = st.sidebar.slider("عدد النتائج المعروضة:", 1, 10, 5)
    
    filtered_df = df[df[control_col] == search]
    
    if not filtered_df.empty:
        row = filtered_df.iloc[0]
        st.subheader(f"ECC Control: {search}")
        st.info(row[source_col])
        
        st.markdown("### Mapping Results")
        mappings = extract_mappings(row, df, top_k)
        
        for m in mappings:
            with st.expander(f"#{m['rank']} | {m['mapping']} - Score: {m['final']}%"):
                st.markdown(f"**NIST Text:** {m['text']}")
                st.success(f"**AI Justification:**\n{m['justification']}")
                st.warning(f"**Differences noticed by AI:**\n{m['differences']}")
    else:
        st.warning("لا توجد بيانات لهذا الضابط.")
