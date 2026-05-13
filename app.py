import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

st.set_page_config(
    page_title="Control Mapping Viewer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# CSS STYLE - مع تحسين القائمة الجانبية
# -------------------------
st.markdown("""
<style>
body {
    background-color: #f5f5f5;
}

.block-container {
    padding-top: 2rem;
    padding-left: 2rem;
    padding-right: 1rem;
}

/* ========== تحسين القائمة الجانبية ========== */
[data-testid="stSidebar"] {
    min-width: 320px;
    max-width: 320px;
    background-color: #f8fafc;
    border-right: 1px solid #e2e8f0;
    transition: all 0.3s ease;
}

@media (max-width: 1200px) {
    [data-testid="stSidebar"] {
        min-width: 280px;
        max-width: 280px;
    }
}

/* تحسين محتوى القائمة الجانبية */
[data-testid="stSidebar"] .element-container {
    margin-bottom: 0.5rem;
}

/* تحسين حقل البحث */
[data-testid="stSidebar"] [data-testid="stTextInput"] {
    margin-bottom: 1rem;
}

[data-testid="stSidebar"] [data-testid="stTextInput"] input {
    border-radius: 8px;
    border: 1px solid #cbd5e1;
    padding: 8px 12px;
    font-size: 13px;
    background-color: white;
}

[data-testid="stSidebar"] [data-testid="stTextInput"] input:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.1);
}

/* تحسين عناصر التحكم (الأزرار) */
[data-testid="stSidebar"] div.stButton > button {
    width: 100%;
    height: auto;
    min-height: 70px;
    text-align: left;
    justify-content: flex-start;
    align-items: flex-start;
    white-space: normal;
    padding: 8px 10px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    background-color: #ffffff;
    color: #1e293b;
    margin-bottom: 6px;
    font-size: 12px;
    line-height: 1.4;
    transition: all 0.2s ease;
    cursor: pointer;
}

[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #eff6ff;
    border-color: #3b82f6;
    transform: translateX(2px);
}

/* نمط العنصر المحدد */
.selected-control-card button {
    background-color: #dbeafe !important;
    border: 1px solid #3b82f6 !important;
    border-left: 3px solid #3b82f6 !important;
}

/* تحسين شريط التمرير في القائمة الجانبية */
[data-testid="stSidebar"] ::-webkit-scrollbar {
    width: 6px;
}

[data-testid="stSidebar"] ::-webkit-scrollbar-track {
    background: #e2e8f0;
    border-radius: 3px;
}

[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
    background: #94a3b8;
    border-radius: 3px;
}

[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
    background: #64748b;
}

/* تحسين عناوين القائمة الجانبية */
.sidebar-title {
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #e2e8f0;
}

/* تحسين الـ Select Box */
[data-testid="stSidebar"] [data-baseweb="select"] {
    margin-bottom: 1rem;
}

[data-testid="stSidebar"] [data-baseweb="select"] div {
    font-size: 13px;
}

/* تحسين الـ Radio buttons */
[data-testid="stSidebar"] [data-testid="stRadio"] {
    margin-bottom: 1rem;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-size: 13px;
}

/* تحسين الـ Slider */
[data-testid="stSidebar"] [data-testid="stSlider"] {
    margin-bottom: 1rem;
}

/* ========== باقي التنسيقات ========== */
.main-title {
    font-size: 48px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0;
}

.subtitle {
    font-size: 18px;
    color: #475569;
    margin-top: -8px;
    margin-bottom: 20px;
}

.control-card {
    padding: 18px;
    border-radius: 0px;
    border-bottom: 1px solid #eee;
    cursor: pointer;
}

.control-card-selected {
    background-color: #dff0ff;
    padding: 18px;
    border-radius: 0px;
    border-bottom: 1px solid #eee;
}

.control-id {
    font-size: 24px;
    font-weight: 800;
    color: #1476d4;
}

.control-text {
    font-size: 18px;
    color: #666;
    line-height: 1.35;
}

.small-muted {
    color: #8a8a8a;
    font-size: 16px;
}

.mapping-card {
    border: 2px solid #75b843;
    border-radius: 6px;
    background-color: #f1faec;
    padding: 14px;
    margin-bottom: 14px;
}

.mapping-title {
    font-size: 18px;
    font-weight: 800;
    color: #1476d4;
}

.rank-pill {
    background-color: #1476d4;
    color: white;
    border-radius: 18px;
    padding: 4px 8px;
    font-weight: 700;
    font-size: 12px;
    margin-right: 10px;
}

.score-line {
    float: right;
    font-size: 12px;
    font-weight: 700;
}

.score-green {
    color: #00a13a;
}

.score-purple {
    color: #7b2cff;
}

.score-blue {
    color: #005cff;
}

.mapping-text {
    clear: both;
    color: #555;
    font-size: 13px;
    line-height: 1.4;
    margin-top: 10px;
}

.graph-box {
    border: 1px solid #d8d8d8;
    background-color: white;
    border-radius: 5px;
    padding: 0px;
}

/* تحسين عرض الأعمدة */
[data-testid="column"] {
    gap: 1rem;
}
</style>
""", unsafe_allow_html=True)


# -------------------------
# HELPERS
# -------------------------
def short_text(text, limit=150):
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "..."


def get_mapping_columns(i):
    if i == 1:
        return {
            "mapping": "NIST mapping",
            "text": "Text",
            "dense": "Dense",
            "sparse": "Sparse",
            "hybrid": "Hybrid",
            "ontology": "Ontology Score",
            "final": "Final Score",
            "confidence": "Confidence match"
        }
    return {
        "mapping": f"NIST mapping {i}",
        "text": f"Text {i}",
        "dense": f"Dense {i}",
        "sparse": f"Sparse {i}",
        "hybrid": f"Hybrid {i}",
        "ontology": f"Ontology Score {i}",
        "final": f"Final Score {i}",
        "confidence": f"Confidence match {i}"
    }


def extract_mappings(row, df, top_k):
    results = []

    for i in range(1, 11):
        cols = get_mapping_columns(i)

        if cols["mapping"] not in df.columns:
            continue

        if pd.isna(row.get(cols["mapping"])):
            continue

        final_score = float(row.get(cols["final"], 0))
        dense = float(row.get(cols["dense"], 0))
        sparse = float(row.get(cols["sparse"], 0))
        hybrid = float(row.get(cols["hybrid"], 0))

        results.append({
            "rank": i,
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "dense": dense,
            "sparse": sparse,
            "hybrid": hybrid,
            "ontology": row.get(cols["ontology"], ""),
            "final": final_score,
            "confidence": str(row.get(cols["confidence"], ""))
        })

    results = sorted(results, key=lambda x: x["final"], reverse=True)
    return results[:top_k]


def create_graph(selected_control, source_text, mappings):
    net = Network(
        height="580px",
        width="100%",
        bgcolor="#ffffff",
        directed=False
    )

    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "font": {
          "size": 18,
          "face": "arial",
          "color": "white",
          "strokeWidth": 0
        }
      },
        "edges": {
        "color": {
            "color": "#bdbdbd",
            "highlight": "#19a34a"
        },
        "smooth": false,

        "font": {
            "size": 16,
            "face": "arial",
            "strokeWidth": 3,
            "strokeColor": "#ffffff"
        },

        "scaling": {
            "label": {
            "enabled": false
            }
        }
        },
      "physics": {
        "enabled": true,
        "solver": "repulsion",
        "repulsion": {
          "nodeDistance": 180,
          "centralGravity": 0.18,
          "springLength": 160,
          "springConstant": 0.04,
          "damping": 0.09
        },
        "stabilization": {
          "enabled": true,
          "iterations": 200
        }
      }
    }
    """)

    net.add_node(
        selected_control,
        label=selected_control,
        title=html.escape(source_text),
        color={
            "background": "#1687d9",
            "border": "#0b4f8a"
        },
        font={
            "color": "#ffffff",
            "size": 50,
            "face": "arial",
            "bold": True
        },
        shape="circle",
        size=150
    )

    for item in mappings:
        score_percent = item["final"] * 100

        net.add_node(
            item["mapping"],
            label=item["mapping"],
            title=html.escape(item["text"]),
            color={
                "background": "#328a36",
                "border": "#1b1b1b"
            },
        font={
            "color": "#ffffff",
            "size": 20,
            "face": "arial",
            "bold": True
        },
            shape="circle",
            size=30
        )

        relation = "PRIMARY SUBSET" if item["rank"] <= 3 else "SECONDARY SUBSET"

        # Colors
        if relation == "PRIMARY SUBSET":
            edge_color = "#10b981"   # green
        else:
            edge_color = "#f59e0b"   # orange

        net.add_edge(
            selected_control,
            item["mapping"],
            
            # SHOW BOTH TEXT + SCORE
            label=f"{relation}\n{score_percent:.0f}%",
            
            title=f"{relation} | {item['confidence']}",
            
            value=max(score_percent / 25, 1),
            width=2 if relation == "PRIMARY SUBSET" else 2,

            color={
                "color": "#dcd2d2",
                "highlight": edge_color,
                "hover": edge_color
            },

            font={
                "color": edge_color,
                "size": 16,
                "face": "arial",
                "strokeWidth": 1,
                "strokeColor": "#ffffff",
                "align": "middle"
            }
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, "r", encoding="utf-8") as f:
            return f.read()


# -------------------------
# تحميل الملف تلقائياً
# -------------------------
# اسم الملف المطلوب
CSV_FILE_NAME = "final_owl_ontology_refined_mappings.csv"

# البحث عن الملف في نفس مجلد الكود
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, CSV_FILE_NAME)

# محاولة فتح الملف
try:
    df = pd.read_csv(file_path)
    st.success(f"✅ تم تحميل الملف بنجاح: {CSV_FILE_NAME}")
except FileNotFoundError:
    st.error(f"❌ خطأ: لم يتم العثور على الملف '{CSV_FILE_NAME}' في نفس مجلد الكود")
    st.info(f"الرجاء التأكد من وجود الملف في المسار: {file_path}")
    st.stop()
except Exception as e:
    st.error(f"❌ خطأ في قراءة الملف: {str(e)}")
    st.stop()

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.markdown('<div class="sidebar-title">📋 Select Standard</div>', unsafe_allow_html=True)

standard = st.sidebar.selectbox(
    "",
    ["ECC (Essential Cybersecurity Controls)"],
    label_visibility="collapsed"
)

st.sidebar.markdown('<div class="sidebar-title">📊 View Mode</div>', unsafe_allow_html=True)

tab_choice = st.sidebar.radio(
    "",
    ["📊 Mappings", "📈 Analytics"],
    horizontal=True
)

# -------------------------
# التحقق من الأعمدة المطلوبة
# -------------------------
control_col = "ECC id control"
source_col = "Source Text"

if control_col not in df.columns or source_col not in df.columns:
    st.error(f"❌ ملف CSV يجب أن يحتوي على أعمدة: '{control_col}' و '{source_col}'")
    st.info(f"الأعمدة الموجودة: {list(df.columns)}")
    st.stop()

controls_df = df[[control_col, source_col]].dropna().copy()
controls_df[control_col] = controls_df[control_col].astype(str)

st.sidebar.markdown(f'<div class="sidebar-title">🎮 Controls ({len(controls_df)})</div>', unsafe_allow_html=True)

# Search box
search = st.sidebar.text_input(
    "🔍",
    placeholder="Search by control number (e.g., 2.4)",
    label_visibility="collapsed"
)

if search:
    controls_df = controls_df[
        controls_df[control_col].str.contains(search, case=False, na=False)
    ]

# Keep selected control
if "selected_control" not in st.session_state:
    st.session_state.selected_control = controls_df[control_col].astype(str).iloc[0]


def count_mappings(row):
    count = 0
    for i in range(1, 11):
        col = "NIST mapping" if i == 1 else f"NIST mapping {i}"
        if col in df.columns and pd.notna(row.get(col)):
            count += 1
    return count


# Control list container
control_box = st.sidebar.container(height=500, border=True)

with control_box:
    for i, r in controls_df.iterrows():
        cid = str(r[control_col])
        preview = short_text(r[source_col], 120)

        full_row = df[df[control_col].astype(str) == cid].iloc[0]
        count = count_mappings(full_row)

        # تنسيق النص المعروض في الزر
        label = f"**{cid}**  \n{preview}  \n🔗 {count} mappings"

        if cid == st.session_state.selected_control:
            st.markdown('<div class="selected-control-card">', unsafe_allow_html=True)

        if st.button(label, key=f"control_btn_{i}"):
            st.session_state.selected_control = cid
            st.rerun()

        if cid == st.session_state.selected_control:
            st.markdown("</div>", unsafe_allow_html=True)


selected_control = st.session_state.selected_control

row = df[df[control_col].astype(str) == selected_control].iloc[0]
source_text = str(row[source_col])

st.sidebar.markdown('<div class="sidebar-title">⚙️ Settings</div>', unsafe_allow_html=True)
top_k = st.sidebar.slider("Top-K Mappings:", 1, 10, 10)

# تعريف mappings قبل استخدامه
mappings = extract_mappings(row, df, top_k)


# -------------------------
# MAIN HEADER
# -------------------------
if tab_choice == "📊 Mappings":
    st.markdown('<div class="main-title">🗺️ Control Mapping Viewer</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="subtitle">🎯 Viewing mappings for: <b>{selected_control}</b> ({len(mappings)} mappings found)</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns([3.2, 1.7])

    # -------------------------
    # GRAPH
    # -------------------------
    with left:
        graph_html = create_graph(selected_control, source_text, mappings)
        st.markdown('<div class="graph-box">', unsafe_allow_html=True)
        components.html(graph_html, height=610, scrolling=False)
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------
    # RIGHT CARDS
    # -------------------------
    with right:
        for idx, item in enumerate(mappings, start=1):
            final_percent = item["final"] * 100
            dense_percent = item["dense"] * 100
            sparse_percent = item["sparse"] * 100
            hybrid_percent = item["hybrid"] * 100

            st.markdown(
                f"""
                <div class="mapping-card">
                    <div>
                        <span class="rank-pill">#{idx}</span>
                        <span class="mapping-title">{item['mapping']}</span>
                        <span class="score-line">
                            <span class="score-green">E:{final_percent:.0f}%</span>
                            <span class="score-purple"> O:{sparse_percent:.0f}%</span>
                            <span class="score-blue"> J:{hybrid_percent:.0f}%</span>
                        </span>
                    </div>
                    <div class="mapping-text">
                        {short_text(item['text'], 210)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# -------------------------
# ANALYTICS TAB
# -------------------------
elif tab_choice == "📈 Analytics":

    def get_all_mappings(df):
        all_items = []

        for _, row in df.iterrows():
            control_id = str(row[control_col])

            for i in range(1, 11):
                cols = get_mapping_columns(i)

                if cols["mapping"] not in df.columns:
                    continue

                mapping_value = row.get(cols["mapping"])

                if pd.isna(mapping_value) or str(mapping_value).strip() == "":
                    continue

                all_items.append({
                    "control": control_id,
                    "mapping": str(mapping_value),
                    "dense": float(row.get(cols["dense"], 0) or 0),
                    "sparse": float(row.get(cols["sparse"], 0) or 0),
                    "hybrid": float(row.get(cols["hybrid"], 0) or 0),
                    "ontology": float(row.get(cols["ontology"], 0) or 0),
                    "final": float(row.get(cols["final"], 0) or 0),
                    "confidence": str(row.get(cols["confidence"], "")),
                    "rank": i
                })

        return pd.DataFrame(all_items)

    analytics_all = get_all_mappings(df)

    total_controls = len(df)
    total_mappings_count = len(analytics_all)
    avg_mappings = total_mappings_count / total_controls if total_controls else 0

    controls_with_mappings = analytics_all["control"].nunique()
    controls_without_mappings = total_controls - controls_with_mappings

    avg_embedding = analytics_all["dense"].mean() * 100 if not analytics_all.empty else 0
    avg_ontology = analytics_all["ontology"].mean() * 100 if not analytics_all.empty else 0
    avg_jaccard = analytics_all["sparse"].mean() * 100 if not analytics_all.empty else 0

    with_counts = controls_with_mappings / total_controls * 100 if total_controls else 0
    without_counts = controls_without_mappings / total_controls * 100 if total_controls else 0

    st.markdown("""
    <style>
    .analytics-card {
        background: white;
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 26px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 1px solid #eeeeee;
    }

    .section-title {
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 18px;
        color: #0f172a;
        border-bottom: 3px solid #e5e7eb;
        padding-bottom: 16px;
    }

    .metric-box {
        border: 2px solid #e5e7eb;
        border-radius: 10px;
        padding: 28px;
        text-align: center;
        background: #f8fafc;
    }

    .metric-number {
        font-size: 52px;
        font-weight: 900;
        color: #1f2937;
    }

    .metric-label {
        font-size: 20px;
        color: #596579;
        font-weight: 600;
    }

    .gap-warning {
        border: 3px solid #f59e0b;
        background: #fff9e8;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
    }

    .gap-success {
        border: 3px solid #10b981;
        background: #e9fff3;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
    }

    .orange-number {
        font-size: 54px;
        font-weight: 900;
        color: #f59e0b;
    }

    .green-number {
        font-size: 54px;
        font-weight: 900;
        color: #10b981;
    }

    .progress-bg {
        width: 100%;
        height: 12px;
        background: #e5e7eb;
        border-radius: 20px;
        overflow: hidden;
        margin-top: 12px;
    }

    .progress-blue {
        height: 100%;
        background: linear-gradient(90deg, #3b82f6, #6366f1);
        border-radius: 20px;
    }

    .progress-purple {
        height: 100%;
        background: #8b5cf6;
        border-radius: 20px;
    }

    .progress-green {
        height: 100%;
        background: #10b981;
        border-radius: 20px;
    }

    .progress-orange {
        height: 100%;
        background: #f59e0b;
        border-radius: 20px;
    }

    .progress-red {
        height: 100%;
        background: #ef4444;
        border-radius: 20px;
    }

    .relation-box {
        border: 2px solid #e5e7eb;
        border-radius: 10px;
        padding: 28px;
        background: #f8fafc;
    }

    .relation-title {
        text-align: center;
        font-size: 22px;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 24px;
    }

    .relation-row {
        margin-bottom: 24px;
        font-size: 18px;
        font-weight: 700;
        color: #334155;
    }

    .relation-value {
        float: right;
        color: #64748b;
        font-weight: 600;
    }

    .reciprocal-box {
        border: 3px solid #10b981;
        background: #e9fff3;
        border-radius: 14px;
        padding: 36px;
        display: flex;
        align-items: center;
        justify-content: space-around;
        flex-wrap: wrap;
        gap: 20px;
    }

    .big-green {
        font-size: 86px;
        font-weight: 900;
        color: #10b981;
        text-align: center;
    }

    .table-head {
        background: #f1f3f6;
        font-weight: 800;
        padding: 18px;
        border-bottom: 2px solid #e5e7eb;
    }

    .table-row {
        padding: 18px;
        border-bottom: 1px solid #e5e7eb;
        font-size: 18px;
        font-weight: 600;
    }
    
    .circular-progress {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        border: 18px solid #e2e8f0;
        border-top-color: #10b981;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        font-weight: 900;
        color: #10b981;
    }
    </style>
    """, unsafe_allow_html=True)

    # OVERVIEW
    st.markdown('<div class="analytics-card"><div class="section-title">📊 Overview</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">{total_controls}</div>
            <div class="metric-label">Total ECC Controls</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">{total_mappings_count}</div>
            <div class="metric-label">Total Recommended Mappings</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">{avg_mappings:.1f}</div>
            <div class="metric-label">Avg Mappings per Control</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # GAP ANALYSIS
    st.markdown('<div class="analytics-card"><div class="section-title">⚠️ Gap Analysis</div>', unsafe_allow_html=True)

    g1, g2 = st.columns(2)

    with g1:
        st.markdown(f"""
        <div class="gap-warning">
            <div class="orange-number">{controls_without_mappings}</div>
            <div class="metric-label">Controls with 0 Mappings</div>
            <div style="color:#94a3b8;font-weight:700;margin-top:10px;">{without_counts:.1f}% of total</div>
        </div>
        """, unsafe_allow_html=True)

    with g2:
        st.markdown(f"""
        <div class="gap-success">
            <div class="green-number">{controls_with_mappings}</div>
            <div class="metric-label">Controls with Mappings</div>
            <div style="color:#94a3b8;font-weight:700;margin-top:10px;">{with_counts:.1f}% coverage</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # AVERAGE SIMILARITY SCORES
    st.markdown('<div class="analytics-card"><div class="section-title">📈 Average Similarity Scores</div>', unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)

    with s1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">{avg_embedding:.1f}%</div>
            <div class="metric-label">Avg Embedding Score</div>
            <div class="progress-bg"><div class="progress-blue" style="width:{min(avg_embedding, 100)}%;"></div></div>
        </div>
        """, unsafe_allow_html=True)

    with s2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">{avg_ontology:.1f}%</div>
            <div class="metric-label">Avg Ontology Score</div>
            <div class="progress-bg"><div class="progress-purple" style="width:{min(avg_ontology, 100)}%;"></div></div>
        </div>
        """, unsafe_allow_html=True)

    with s3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-number">{avg_jaccard:.1f}%</div>
            <div class="metric-label">Avg Jaccard Similarity</div>
            <div class="progress-bg"><div class="progress-green" style="width:{min(avg_jaccard, 100)}%;"></div></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # RELATIONSHIP CLASSIFICATION
    st.markdown('<div class="analytics-card"><div class="section-title">🔄 Relationship Classification</div>', unsafe_allow_html=True)

    if total_mappings_count > 0:
        primary_count = len(analytics_all[analytics_all["rank"] <= 3])
        secondary_count = len(analytics_all[analytics_all["rank"] > 3])
        primary_pct = (primary_count / total_mappings_count * 100) if total_mappings_count else 0
        secondary_pct = (secondary_count / total_mappings_count * 100) if total_mappings_count else 0
    else:
        primary_count = secondary_count = primary_pct = secondary_pct = 0

    r1, r2 = st.columns(2)

    with r1:
        st.markdown(f"""
        <div class="relation-box">
            <div class="relation-title">🎯 Primary vs Secondary</div>
            <div class="relation-row">
                <span>🔹 Primary (Rank 1-3)</span>
                <span class="relation-value">{primary_count} ({primary_pct:.1f}%)</span>
            </div>
            <div class="progress-bg"><div class="progress-green" style="width:{primary_pct:.1f}%;"></div></div>
            <div class="relation-row" style="margin-top:20px;">
                <span>🔸 Secondary (Rank 4-10)</span>
                <span class="relation-value">{secondary_count} ({secondary_pct:.1f}%)</span>
            </div>
            <div class="progress-bg"><div class="progress-orange" style="width:{secondary_pct:.1f}%;"></div></div>
        </div>
        """, unsafe_allow_html=True)

    with r2:
        # حساب توزيع الثقة
        confidence_counts = analytics_all["confidence"].value_counts()
        confidence_data = ""
        colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444"]
        color_idx = 0
        for conf, cnt in confidence_counts.items():
            pct = (cnt / total_mappings_count * 100) if total_mappings_count else 0
            confidence_data += f"""
            <div class="relation-row">
                <span>🏷️ {conf}</span>
                <span class="relation-value">{cnt} ({pct:.1f}%)</span>
            </div>
            <div class="progress-bg"><div class="progress-purple" style="width:{pct:.1f}%;background:{colors[color_idx % len(colors)]};"></div></div>
            """
            color_idx += 1
        
        st.markdown(f"""
        <div class="relation-box">
            <div class="relation-title">📊 Confidence Distribution</div>
            {confidence_data if confidence_data else '<div class="relation-row">No confidence data available</div>'}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # DISTRIBUTION TABLE
    st.markdown('<div class="analytics-card"><div class="section-title">📊 Distribution of Recommended Mappings</div>', unsafe_allow_html=True)

    mapping_counts = []

    for _, row in df.iterrows():
        c = 0
        for i in range(1, 11):
            col = "NIST mapping" if i == 1 else f"NIST mapping {i}"
            if col in df.columns and pd.notna(row.get(col)):
                c += 1
        mapping_counts.append(c)

    dist = pd.Series(mapping_counts).value_counts().sort_index()

    st.markdown("""
    <div style="display:grid;grid-template-columns:2fr 1.6fr 1fr 1fr;background:#f1f3f6;border-radius:8px;">
        <div class="table-head">📌 Recommended Mappings</div>
        <div class="table-head">📈 Number of Controls</div>
        <div class="table-head">📊 Percentage</div>
        <div class="table-head">🎨 Visual</div>
    </div>
    """, unsafe_allow_html=True)

    for num_maps, count in dist.items():
        pct = (count / total_controls * 100) if total_controls else 0

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:2fr 1.6fr 1fr 1fr;">
            <div class="table-row">{num_maps}</div>
            <div class="table-row">{count}</div>
            <div class="table-row">{pct:.1f}%</div>
            <div class="table-row">
                <div class="progress-bg">
                    <div class="progress-blue" style="width:{min(pct, 100)}%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
