import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# إعداد الصفحة لتكون عريضة
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# -------------------------
# وظيفة إزالة الـ Parent Controls
# -------------------------
def remove_parent_controls(df):
    # تحويل العمود إلى نص
    ids = df["ECC id control"].astype(str).str.strip()
    # الاحتفاظ فقط بالمعرفات التي تبدأ بحرف (وليست رقماً)
    mask = ids.str.match(r'^[A-Z]', na=False)
    return df[mask]

# -------------------------
# وظائف استخراج البيانات
# -------------------------
def get_mapping_columns(i):
    if i == 1:
        return {
            "mapping": "NIST mapping",
            "text": "Text",
            "final": "Final Score",
            "commonality": "Commonality",
            "justification": "Justification",
            "differences": "Differences"
        }
    else:
        return {
            "mapping": f"NIST mapping {i}",
            "text": f"Text {i}",
            "final": f"Final Score {i}",
            "commonality": f"Commonality {i}",
            "justification": f"Justification {i}",
            "differences": f"Differences {i}"
        }

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
        
        # جلب Commonality مع قيمة افتراضية
        commonality_value = row.get(cols["commonality"], "")
        if pd.isna(commonality_value) or commonality_value == "":
            commonality_value = "Both controls share related cybersecurity objectives."
        
        # جلب Justification مع قيمة افتراضية
        justification_value = row.get(cols["justification"], "")
        if pd.isna(justification_value) or justification_value == "":
            justification_value = "The controls contain similar cybersecurity concepts."
        
        # جلب Differences مع قيمة افتراضية
        differences_value = row.get(cols["differences"], "")
        if pd.isna(differences_value) or differences_value == "":
            differences_value = "The controls differ in implementation focus and specific requirements."
        
        results.append({
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "final": score,
            "commonality": str(commonality_value),
            "justification": str(justification_value),
            "differences": str(differences_value)
        })
    # ترتيب من الأقرب (أعلى درجة) للأبعد
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

def create_graph(selected_id, source_text, mappings):
    # إنشاء الشبكة مع خلفية بيضاء
    net = Network(height="750px", width="100%", bgcolor="#ffffff")
    
    # إعدادات الفيزياء لضمان التوزيع الدائري
    net.set_options("""
    {
      "nodes": {
        "font": { "size": 18, "face": "arial" },
        "borderWidth": 2
      },
      "edges": {
        "font": { "size": 16, "align": "middle", "color": "#1476d4", "strokeWidth": 4, "strokeColor": "#ffffff" },
        "color": { "color": "#d3dbe3" },
        "smooth": false
      },
      "physics": {
        "forceAtlas2Based": { "gravitationalConstant": -100, "springLength": 200 },
        "solver": "forceAtlas2Based",
        "stabilization": { "enabled": true, "iterations": 1000 }
      }
    }
    """)

    # العقدة المركزية
    net.add_node(selected_id, label=selected_id, title=html.escape(source_text), 
                 color="#1687d9", size=45, shape="circle", 
                 font={'color': 'white', 'bold': True, 'size': 22})

    # العقد المحيطة
    for idx, item in enumerate(mappings):
        rank_label = f"#{idx + 1}"
        edge_width = max(1, 10 - idx)
        
        net.add_node(item["mapping"], label=item["mapping"], title=html.escape(item["text"]), 
                     color="#328a36", size=32, shape="circle", font={'color': 'white'})
        
        net.add_edge(selected_id, item["mapping"], label=rank_label, width=edge_width)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# -------------------------
# الواجهة الرئيسية
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    # إزالة الـ Parent Controls (التي تبدأ بأرقام)
    df = remove_parent_controls(df)
    
    # قائمة التحكم الجانبية لاختيار الـ ID
    st.sidebar.title("Controls List")
    selected_id = st.sidebar.selectbox("Select Control ID:", df["ECC id control"].unique())
    
    st.title("Control Mapping Viewer")
    st.write(f"Viewing: **{selected_id}**")
    
    # جلب البيانات للعنصر المختار
    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    mappings = extract_mappings(row, df)
    
    # عرض الرسم البياني
    graph_html = create_graph(str(selected_id), str(row["Source Text"]), mappings)
    components.html(graph_html, height=800)
    
    # عرض التفسيرات من AI
    if mappings:
        st.subheader("AI Explanations")
        st.write("Commonality, Justification, and Differences for each mapping")
        
        for idx, item in enumerate(mappings):
            with st.expander(f"#{idx + 1} - {item['mapping']}"):
                st.markdown(f"**Commonality:** {item['commonality']}")
                st.markdown(f"**Justification:** {item['justification']}")
                st.markdown(f"**Differences:** {item['differences']}")
    else:
        st.info("No mappings found for this control.")

else:
    st.error("Data file not found. Please ensure the CSV is in the same directory.")
