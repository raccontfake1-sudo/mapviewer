import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# 1. إعدادات الصفحة
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# -------------------------
# HELPERS
# -------------------------
def get_mapping_columns(i):
    if i == 1: return {"mapping": "NIST mapping", "text": "Text", "final": "Final Score"}
    return {"mapping": f"NIST mapping {i}", "text": f"Text {i}", "final": f"Final Score {i}"}

def extract_mappings(row, df, top_k=10):
    results = []
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        if cols["mapping"] not in df.columns or pd.isna(row.get(cols["mapping"])): continue
        try:
            val = str(row.get(cols["final"], 0)).replace('%', '')
            score = float(val) / 100.0 if float(val) > 1.0 else float(val)
        except: score = 0.0
        results.append({
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "final": score
        })
    # ترتيب تنازلي بناءً على السكور (الأقرب أولاً)
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

def create_graph(selected_id, source_text, mappings):
    # إنشاء الشبكة مع تعطيل شريط الأدوات الافتراضي
    net = Network(height="700px", width="100%", bgcolor="#ffffff")
    
    # إعدادات الفيزياء لجعل التوزيع دائرياً ومتساوياً تماماً مثل صورتك
    net.set_options("""
    {
      "nodes": {
        "font": { "size": 18, "face": "arial" },
        "borderWidth": 2
      },
      "edges": {
        "font": { "size": 16, "align": "middle", "color": "#1476d4", "strokeWidth": 5, "strokeColor": "#ffffff" },
        "color": { "color": "#d3dbe3" },
        "smooth": false
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -100,
          "centralGravity": 0.01,
          "springLength": 200,
          "springConstant": 0.08
        },
        "solver": "forceAtlas2Based",
        "stabilization": { "enabled": true, "iterations": 1000 }
      }
    }
    """)

    # العقدة المركزية (الأزرق)
    net.add_node(selected_id, label=selected_id, title=html.escape(source_text), 
                 color="#1687d9", size=45, shape="circle", 
                 font={'color': 'white', 'bold': True, 'size': 22})

    # العقد المحيطة (الأخضر) والأسهم المرقمة
    for idx, item in enumerate(mappings):
        rank_label = f"#{idx + 1}"  # الترقيم من #1 إلى #10
        
        # التحكم في سماكة الخط بناءً على الترتيب (الأول هو الأسمك)
        # يبدأ من 10 للأول ويقل تدريجياً
        edge_width = 10 - idx  
        
        # إضافة العقدة الفرعية
        net.add_node(item["mapping"], label=item["mapping"], title=html.escape(item["text"]), 
                     color="#328a36", size=30, shape="circle", font={'color': 'white'})
        
        # إضافة السهم مع التسمية (#1, #2...) والسمك المتغير
        net.add_edge(selected_id, item["mapping"], label=rank_label, width=edge_width)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, 'r', encoding='utf-8').read()

# -------------------------
# MAIN INTERFACE
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    if "selected_id" not in st.session_state:
        st.session_state.selected_id = str(df["ECC id control"].iloc[0])

    # واجهة العرض
    st.markdown(f"## Control Mapping Viewer")
    st.write(f"Viewing: **{st.session_state.selected_id}**")
    
    # استخراج البيانات المحددة
    row = df[df["ECC id control"].astype(str) == st.session_state.selected_id].iloc[0]
    mappings = extract_mappings(row, df)

    # عرض الرسم البياني
    graph_html = create_graph(st.session_state.selected_id, str(row["Source Text"]), mappings)
    components.html(graph_html, height=750)

else:
    st.error("ملف البيانات غير موجود.")
