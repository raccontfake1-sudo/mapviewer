import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# إعداد الصفحة
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# -------------------------
# 1. دالة الفلتر (للتأكد من وجود بيانات في القائمة)
# -------------------------
def remove_parent_controls(df):
    # نعيد كل البيانات مؤقتاً لنتأكد من ظهور القائمة
    # (يمكنك تعديل هذا الشرط لاحقاً حسب رغبتك)
    return df

# -------------------------
# 2. تعريف أسماء الأعمدة
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

# -------------------------
# 3. استخراج البيانات
# -------------------------
def extract_mappings(row, df, top_k=10):
    results = []
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        if cols["mapping"] not in df.columns or pd.isna(row.get(cols["mapping"])):
            continue
            
        try:
            val = str(row.get(cols["final"], 0)).replace('%', '')
            score = float(val) / 100.0 if float(val) > 1.0 else float(val)
        except:
            score = 0.0
            
        # جلب النصوص (مع استخدام "غير متوفر" كقيمة افتراضية)
        commonality = row.get(cols["commonality"], "")
        justification = row.get(cols["justification"], "")
        differences = row.get(cols["differences"], "")
        
        if pd.isna(commonality) or commonality == "": commonality = "غير متوفر"
        if pd.isna(justification) or justification == "": justification = "غير متوفر"
        if pd.isna(differences) or differences == "": differences = "غير متوفر"
            
        results.append({
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "final": score,
            "commonality": commonality,
            "justification": justification,
            "differences": differences
        })
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

# -------------------------
# 4. رسم الشبكة
# -------------------------
def create_graph(selected_id, source_text, mappings):
    net = Network(height="650px", width="100%", bgcolor="#ffffff")
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": { "gravitationalConstant": -100, "springLength": 200 },
        "solver": "forceAtlas2Based", "stabilization": { "iterations": 1000 }
      },
      "nodes": { "font": { "size": 18, "face": "arial" }, "borderWidth": 2 },
      "edges": { "font": { "size": 16, "align": "middle", "color": "#1476d4" }, "color": "#d3dbe3" }
    }
    """)
    
    # العقدة المركزية
    net.add_node(selected_id, label=selected_id, title=html.escape(source_text), 
                 color="#1687d9", size=45, shape="circle", font={'color': 'white', 'bold': True})

    for idx, item in enumerate(mappings):
        edge_width = max(1, 10 - idx)
        net.add_node(item["mapping"], label=item["mapping"], title=html.escape(item["text"]), 
                     color="#328a36", size=32, shape="circle", font={'color': 'white'})
        net.add_edge(selected_id, item["mapping"], label=f"#{idx+1}", width=edge_width)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# -------------------------
# 5. الواجهة الرئيسية
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    # تطبيق الفلتر (إذا أردت إخفاء بعض المعرفات)
    df = remove_parent_controls(df)
    
    # التأكد من وجود بيانات قبل عرض القائمة
    if df.empty:
        st.error("لا توجد بيانات بعد تطبيق الفلتر. يرجى مراجعة دالة remove_parent_controls")
        st.stop()
    
    st.sidebar.title("Controls List")
    selected_id = st.sidebar.selectbox("Select Control ID:", df["ECC id control"].unique())
    
    st.title("Control Mapping Viewer")
    
    # جلب بيانات الصف المحدد
    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    mappings = extract_mappings(row, df)
    
    # عرض الرسم البياني
    graph_html = create_graph(str(selected_id), str(row["Source Text"]), mappings)
    components.html(graph_html, height=680)
    
    # عرض قسم التفسيرات (بأسلوب Markdown بسيط وواضح)
    st.markdown("## AI Explanations")
    
    if mappings:
        for idx, m in enumerate(mappings):
            # استخدام expander مباشرة بدون HTML معقد
            with st.expander(f"#{idx+1} - {m['mapping']}"):
                # استخدام markdown العادي
                st.markdown(f"**Commonality:** {m['commonality']}")
                st.markdown(f"**Justification:** {m['justification']}")
                st.markdown(f"**Differences:** {m['differences']}")
    else:
        st.info("No detailed mappings found for this control.")
        
else:
    st.error("Data file not found. Please ensure the CSV is in the same directory.")
