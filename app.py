import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os
import re

# إعداد الصفحة لتكون عريضة ومنسقة بمعايير احترافية
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

def extract_mappings(row, df_columns, top_k=10):
    results = []
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        if cols["mapping"] not in df_columns or pd.isna(row.get(cols["mapping"])):
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
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

# -------------------------
# رسم الجراف الاحترافي
# -------------------------
def create_graph(selected_id, source_text, mappings):
    net = Network(height="600px", width="100%", bgcolor="#ffffff")
    
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": { "gravitationalConstant": -160, "springLength": 220, "avoidOverlap": 1 },
        "solver": "forceAtlas2Based", "stabilization": { "iterations": 800 }
      },
      "nodes": { "font": { "face": "arial" }, "borderWidth": 2 },
      "edges": { "font": { "size": 16, "align": "middle", "color": "#1476d4" }, "color": "#d3dbe3" }
    }
    """)
    
    # العقدة المركزية الزرقاء: استخدام شكل box لضمان ظهور رقم الكنترول بداخلها دائماً بوضوح
    net.add_node(
        "MAIN", 
        label=f" {str(selected_id)} ", 
        title=f"<b>Source Text:</b><br>{html.escape(source_text)}", 
        color={"background": "#1687d9", "border": "#106ba9"}, 
        shape="box", 
        margin=15,
        font={"color": "white", "size": 22, "bold": True}
    )

    # إضافة عقد الـ NIST والخطوط بترتيب إجباري من #1 إلى #10
    for idx, item in enumerate(mappings):
        node_id = f"NIST_{item['mapping']}_{idx}"
        edge_width = max(2, 8 - idx)
        
        net.add_node(
            node_id, 
            label=item["mapping"], 
            title=html.escape(item["text"]), 
            color={"background": "#328a36", "border": "#226025"}, 
            shape="box", 
            margin=10,
            font={'color': 'white', 'size': 14, 'bold': True}
        )
        
        # الترتيب المتسلسل الإجباري للخطوط الرابطة من #1 إلى #10
        net.add_edge("MAIN", node_id, label=f"#{idx+1}", width=edge_width)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, 'r', encoding='utf-8') as f:
            return f.read()

# -------------------------
# الواجهة الرئيسية للمشروع
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    st.title("🛡️ Control Mapping Viewer")
    st.write("لوحة تحكم تفاعلية متقدمة لربط وتحليل عناصر التحكم بمواصفات نظام NIST.")
    st.write("---")
    
    # تقسيم الصفحة إلى 3 أعمدة احترافية
    menu_col, graph_col, explain_col = st.columns([1.4, 2.2, 1.6])
    
    with menu_col:
        st.markdown("### 📋 Controls List")
        
        raw_controls = df["ECC id control"].dropna().unique()
        sorted_controls = sorted([str(c) for c in raw_controls], key=natural_sort_key)
        
        # تهيئة "حالة الجلسة" لحفظ الكنترول المختار وتفادي إعادة التحميل العشوائي
        if "selected_control" not in st.session_state:
            st.session_state.selected_control = sorted_controls[0]
            
        # بناء قائمة أزرار تفاعلية بروفيشينال مقاومة للـ Dark Mode ومزودة بـ Scrollbar
        st.markdown(
            """
            <style>
            .scroll-container {
                max-height: 520px;
                overflow-y: auto;
                border: 1px solid #4a4a4a;
                padding: 10px;
                border-radius: 8px;
                background-color: rgba(0,0,0,0.03);
            }
            .control-btn {
                width: 100%;
                text-align: left;
                padding: 10px 15px;
                margin-bottom: 6px;
                border-radius: 6px;
                border: 1px solid #1687d9;
                background-color: transparent;
                font-size: 15px;
                font-weight: bold;
                cursor: pointer;
                transition: 0.3s;
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        
        # إنشاء الأزرار عمودياً بشكل منظم جداً وثابت رقمياً
        st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
        for ctrl in sorted_controls:
            # تمييز الزر النشط حالياً بلون مختلف
            if ctrl == st.session_state.selected_control:
                btn_style = "background-color: #1687d9; color: white;"
            else:
                btn_style = "color: #1687d9;"
                
            if st.button(f"📄 Control {ctrl}", key=f"btn_{ctrl}", use_container_width=True):
                st.session_state.selected_control = ctrl
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    selected_id = st.session_state.selected_control
    
    # جلب السطر المختار بناءً على الزر المضغطوط
    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    mappings = extract_mappings(row, df.columns)

    # عمود عرض الرسم البياني الاحترافي المستقر
    with graph_col:
        st.markdown("### 🕸️ Mapping Visualization")
        graph_html = create_graph(str(selected_id), str(row.get("Source Text", "")), mappings)
        components.html(graph_html, height=620)
        
    # عمود الشروحات على اليمين مرتبة بالتسلسل من 1 إلى 10
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
