import streamlit as st
import pandas as pd

# إعداد واجهة المستخدم
st.set_page_config(layout="wide")
st.title("Control Mapping Viewer")

# تحميل البيانات تلقائياً
@st.cache_data
def load_data():
    df = pd.read_csv('final_ontology_refined_mappings_with_explanations.csv')
    # تحويل العمود لرقدي لضمان الترتيب الصحيح
    df['Similarity Score'] = pd.to_numeric(df['Similarity Score'], errors='coerce')
    # الترتيب من الأعلى (الأقرب) للأقل
    return df.sort_values(by='Similarity Score', ascending=False)

try:
    df = load_data()
    
    # القائمة الجانبية للتحكم
    st.sidebar.header("Settings")
    top_k = st.sidebar.slider("Show Top K Mappings", 1, len(df), 20)
    
    # عرض النتائج المرتبة
    st.write(f"### Displaying Top {top_k} Closest Mappings")
    st.dataframe(df.head(top_k), use_container_width=True)
    
except FileNotFoundError:
    st.error("File not found! Please ensure the CSV is in the same folder.")
