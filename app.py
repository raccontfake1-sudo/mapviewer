import streamlit as st
import pandas as pd

# إعداد واجهة المستخدم
st.set_page_config(layout="wide")
st.title("Control Mapping Viewer")

# تحميل البيانات تلقائياً
@st.cache_data
def load_data():
    file_path = 'final_ontology_refined_mappings_with_explanations.csv.'
    df = pd.read_csv(file_path)
    
    # محاولة إيجاد عمود السكور تلقائياً وترتيبه
    score_columns = ['Similarity Score', 'Final Score', 'Score']
    target_col = next((col for col in score_columns if col in df.columns), None)
    
    if target_col:
        # تنظيف البيانات وتحويلها لرقم
        df[target_col] = pd.to_numeric(df[target_col].astype(str).str.replace('%', ''), errors='coerce')
        # الترتيب من الأعلى للأقل (الأقرب فالأقرب)
        df = df.sort_values(by=target_col, ascending=False)
        
    return df

try:
    df = load_data()
    
    # القائمة الجانبية للبحث والتحكم
    st.sidebar.header("البحث والإعدادات")
    search_query = st.sidebar.text_input("بحث بالـ ID أو الوصف:")
    
    if search_query:
        # البحث في كل الأعمدة
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
    
    # عرض النتائج المرتبة
    st.write(f"### تم إيجاد {len(df)} نتيجة مرتبة حسب الأقرب")
    st.dataframe(df, use_container_width=True)
    
except Exception as e:
    st.error(f"خطأ في قراءة الملف: {e}")
    st.info("تأكد من أن أسماء الأعمدة في ملف الـ CSV مطابقة للكود.")
