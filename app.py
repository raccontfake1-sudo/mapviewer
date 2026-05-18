import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# إعداد الصفحة وتوسيعها
st.set_page_config(
    page_title="Control Mapping Viewer",
    layout="wide"
)

# ---------------------------------
# وظائف الأعمدة
# ---------------------------------
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

# ---------------------------------
# استخراج المابات وترتيبها
# ---------------------------------
def extract_mappings(row, df_columns, top_k=10):
    results = []
    
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        
        # التأكد من أن العمود موجود في ملف البيانات أولاً
        if cols["mapping"] not in df_columns:
            continue
            
        # التأكد من أن السطر يحتوي على قيمة لهذا الماب
        if pd.isna(row.get(cols["mapping"])) or str(row.get(cols["mapping"])).strip() == "":
            continue

        # حساب السكور وتفادي أخطاء الـ string / float
        try:
            val = str(row.get(cols["final"], 0)).replace("%", "").strip()
            score = float(val)
            if score > 1:
                score = score / 100.0
        except:
            score = 0.0

        results.append({
            "rank": i,
            "mapping": str(row.get(cols["mapping"], "")).strip(),
            "text": str(row.get(cols["text"], "")).strip(),
            "score": score,
            "commonality": str(row.get(cols["commonality"], "N/A")),
            "justification": str(row.get(cols["justification"], "N/A")),
            "differences": str(row.get(cols["differences"], "N/A"))
        })
        
    # ضمان ترتيب المابات تصاعدياً من 1 إلى 10 بناءً على الـ rank
    results = sorted(results, key=lambda x: x["rank"])
    return results[:top_k]

# ---------------------------------
# رسم الجراف وتحديث إعدادات الفيزيقا
# ---------------------------------
def create_graph(selected_id, source_text, mappings):
    net = Network(
        height="650px",
        width="100%",
        bgcolor="#ffffff"
    )

    # إعدادات جراف تفاعلية ومريحة للعين
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -150,
          "springLength": 200,
          "avoidOverlap": 1
        },
        "solver": "forceAtlas2Based",
        "stabilization": {
          "iterations": 500
        }
      },
      "nodes": {
        "borderWidth": 2,
        "font": {
          "size": 16,
          "face": "tahoma"
        }
      },
      "edges": {
        "font": {
          "size": 14,
          "align": "middle",
          "color": "#1476d4"
        },
        "color": "#d3dbe3",
        "smooth": true
      }
    }
    """)

    # العقدة الرئيسية (الدائرة الزرقاء الكبيرة) - تعرض رقم الكنترول فقط في الـ label
    net.add_node(
        "MAIN",
        label=str(selected_id), # يعرض رقم الكنترول فقط هنا
        title=f"<b>Source Control Text:</b><br>{html.escape(source_text)}", # النص يظهر فقط عند الوقوف بالماوس فوق الدائرة
        color="#1687d9",
        size=50,
        shape="dot",
        font={"color": "white", "size": 24, "bold": True}
    )

    # العقد الفرعية المربوطة (NIST mappings) مرتبة تلقائياً
    for item in mappings:
        node_id = f"{item['mapping']}_{item['rank']}"
        
        net.add_node(
            node_id,
            label=item["mapping"],
            title=f"<b>NIST Text:</b><br>{html.escape(item['text'])}<br><b>Match Score:</b> {item['score']:.2%}",
            color="#328a36",
            shape="box",  
            font={"color": "white", "size": 14},
            margin=10
        )

        # إضافة الخط الرابط مع إظهار الترتيب بشكل منظم
        net.add_edge(
            "MAIN",
            node_id,
            label=f"Rank {item['rank']}",
            title=f"Similarity: {item['score']:.2%}",
            width=2
        )

    # حفظ وعرض الجراف في ملف مؤقت
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, "r", encoding="utf-8") as f:
            html_content = f.read()
            
    try:
        os.unlink(tmp.name)
    except:
        pass

    return html_content

# ---------------------------------
# الملف الرئيسي وعملية القراءة
# ---------------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]

    st.title("🛡️ Control Mapping Viewer")
    st.write("تعرض هذه اللوحة التفاعلية الربط والتحليل بين عناصر التحكم والمواصفات القياسية لنظام NIST.")
    st.write("---")

    # تقسيم الصفحة بشكل متناسق
    menu_col, graph_col, explain_col = st.columns([1, 2, 1.2])

    with menu_col:
        st.subheader("📋 Control List")
        control_list = df["ECC id control"].dropna().unique()
        
        selected_control = st.selectbox(
            "اختر معرف التحكم (Control ID):",
            control_list
        )

    # جلب السطر المختار بناءً على التحكم
    selected_row = df[df["ECC id control"] == selected_control].iloc[0]
    
    # استخراج المابات وترتيبها تصاعدياً
    mappings = extract_mappings(selected_row, df.columns)

    # جزء عرض الجراف التفاعلي
    with graph_col:
        st.subheader("🕸️ Mapping Visualization")
        
        source_text_val = str(selected_row.get("Source Text", "No source text available"))
        
        graph_html = create_graph(
            selected_control,
            source_text_val,
            mappings
        )

        components.html(graph_html, height=650)

    # جزء الشرح والتحليل مرتب من 1 إلى 10
    with explain_col:
        st.subheader("🤖 AI Explanations")
        
        if not mappings:
            st.info("لا توجد مابات (Mappings) متوفرة لهذا العنصر.")
        
        for item in mappings:
            # القوائم تظهر هنا مرتبة تماماً بالترتيب الصحيح المتناسق مع الجراف
            with st.expander(f"🏅 #{item['rank']} - {item['mapping']}", expanded=(item['rank'] == 1)):
                st.markdown(f"**Match Score:** `{item['score']:.2%}`")
                st.markdown(f"**Commonality:**\n{item['commonality']}")
                st.markdown(f"**Justification:**\n{item['justification']}")
                st.markdown(f"**Differences:**\n{item['differences']}")

else:
    st.error(f"⚠️ تعذر العثور على ملف البيانات: `{DATA_FILE}`. يرجى التأكد من وجود الملف في نفس مسار المشروع.")
