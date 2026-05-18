import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os
import re

# إعداد الصفحة لتكون عريضة ومنسقة
st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

# -------------------------
# وظيفة لترتيب الأرقام المتسلسلة (مثل 1.1 و 1.1.1) بشكل صحيح
# -------------------------
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

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
        if cols["mapping"] not in df.columns or pd.isna(row.get(cols["mapping"])):
            continue
        try:
            val = str(row.get(cols["final"], 0)).replace('%', '')
            score = float(val) / 100.0 if float(val) > 1.0 else float(val)
        except:
            score = 0.0
        
        commonality_val = row.get(cols["commonality"], "")
        justification_val = row.get(cols["justification"], "")
        
        differences_val = row.get(cols["differences"], "")
        if pd.isna(differences_val) or differences_val == "":
            differences_val = "The controls differ in implementation focus and specific requirements."
        
        results.append({
            "mapping": str(row.get(cols["mapping"], "")).strip(),
            "text": str(row.get(cols["text"], "")).strip(),
            "final": score,
            "commonality": str(commonality_val) if not pd.isna(commonality_val) else "N/A",
            "justification": str(justification_val) if not pd.isna(justification_val) else "N/A",
            "differences": str(differences_val)
        })
    # ترتيب المابات الفرعية بناءً على السكور الأعلى
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

# -------------------------
# رسم الجراف
# -------------------------
def create_graph(selected_id, source_text, mappings):
    net = Network(height="650px", width="100%", bgcolor="#ffffff")
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": { "gravitationalConstant": -120, "springLength": 220 },
        "solver": "forceAtlas2Based", "stabilization": { "iterations": 1000 }
      },
      "nodes": { "font": { "size": 18, "face": "arial" }, "borderWidth": 2 },
      "edges": { "font": { "size": 16, "align": "middle", "color": "#1476d4" }, "color": "#d3dbe3" }
    }
    """)
    
    # التعديل: الدائرة المركزية الزرقاء الحين يظهر داخلها رقم الكنترول (selected_id) فقط
    net.add_node(
        selected_id, 
        label=str(selected_id), # يعرض رقم الكنترول فقط بالداخل
        title=html.escape(source_text), 
        color="#1687d9", 
        size=55, 
        shape="dot", # تم تغييرها إلى dot ليتناسق النص بالمنتصف تماماً
        font={"color": "white", "size": 20, "bold": True}
    )

    for idx, item in enumerate(mappings):
        edge_width = max(1, 10 - idx)
        
        # العقد الخضراء (NIST)
        net.add_node(
            item["mapping"], 
            label=item["mapping"], 
            title=html.escape(item["text"]), 
            color="#328a36", 
            size=35, 
            shape="circle", 
            font={'color': 'white'}
        )
        
        # الخط الرابط يوضح الترتيب من #1 إلى #10
        net.add_edge(selected_id, item["mapping"], label=f"#{idx+1}", width=edge_width)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, 'r', encoding='utf-8') as f:
            return f.read()

# -------------------------
# الواجهة الرئيسية
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    st.title("Control Mapping Viewer")
    st.write("---")
    
    # تقسيم الصفحة إلى أعمدة: عمود للأزرار وعمود للجراف وعمود للشروحات
    menu_col, graph_col, explain_col = st.columns([1, 2, 1.2])
    
    # التعديل: قائمة الكنترولز أزرار تحت بعضها في الصفحة الرئيسية ومرتبة تسلسلياً
    with menu_col:
        st.markdown("### 📋 Controls List")
        
        # جلب الكنترولز وعمل ترتيب طبيعي وذكي لها (1.1 -> 1.1.1 -> 1.1.2)
        raw_controls = df["ECC id control"].dropna().unique()
        sorted_controls = sorted([str(c) for c in raw_controls], key=natural_sort_key)
        
        # الأزرار تظهر تحت بعضها وتختار منها مباشرة بنقرة واحدة
        selected_id = st.radio(
            "Select Control ID:",
            sorted_controls
        )
    
    # جلب بيانات السطر المختار
    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    mappings = extract_mappings(row, df)

    # عمود عرض الرسم البياني (الجراف)
    with graph_col:
        st.markdown("### 🕸️ Mapping Visualization")
        graph_html = create_graph(str(selected_id), str(row["Source Text"]), mappings)
        components.html(graph_html, height=650)
        
    # عمود تفاصيل تفاسير الذكاء الاصطناعي مرتبة من 1 إلى 10
    with explain_col:
        st.markdown("### 🤖 AI Explanations")
        for idx, item in enumerate(mappings):
            with st.expander(f"🏅 #{idx+1} - {item['mapping']}", expanded=(idx == 0)):
                st.markdown(f"**Match Score:** `{item['final']:.2%}`")
                st.markdown(f"**Commonality:**\n{item['commonality']}")
                st.markdown(f"**Justification:**\n{item['justification']}")
                st.markdown(f"**Differences:**\n{item['differences']}")

else:
    st.error(f"Data file '{DATA_FILE}' not found.")
