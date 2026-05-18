import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os
import math

# إعداد الصفحة
st.set_page_config(
    page_title="Control Mapping Viewer",
    layout="wide"
)

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

# -------------------------
# استخراج المابات
# -------------------------
def extract_mappings(row, df, top_k=10):

    results = []

    for i in range(1, 11):

        cols = get_mapping_columns(i)

        if cols["mapping"] not in df.columns:
            continue

        if pd.isna(row.get(cols["mapping"])):
            continue

        results.append({

            "mapping": str(
                row.get(cols["mapping"], "")
            ),

            "text": str(
                row.get(cols["text"], "")
            ),

            "commonality": str(
                row.get(cols["commonality"], "N/A")
            ),

            "justification": str(
                row.get(cols["justification"], "N/A")
            ),

            "differences": str(
                row.get(cols["differences"], "N/A")
            )
        })

    return results[:top_k]

# -------------------------
# رسم الـ Graph
# -------------------------
def create_graph(selected_id, source_text, mappings):

    net = Network(
        height="750px",
        width="100%",
        bgcolor="#ffffff"
    )

    net.barnes_hut()

    # ---------------------------------
    # الدائرة الزرقاء الرئيسية
    # ---------------------------------
    net.add_node(

        "MAIN",

        label=str(selected_id),

        title=html.escape(
            source_text
        ),

        color="#1687d9",

        size=90,

        shape="dot",

        font={
            "color": "white",
            "size": 30
        }
    )

    # ---------------------------------
    # الكنترولز حول الدائرة
    # ---------------------------------
    for idx, item in enumerate(mappings):

        node_id = (
            f"{item['mapping']}_{idx}"
        )

        net.add_node(

            node_id,

            label=item["mapping"],

            title=html.escape(
                item["text"]
            ),

            color="#328a36",

            size=35,

            shape="circle",

            font={
                "color": "white",
                "size": 18
            }
        )

        # الهاشتاقات مرتبة
        net.add_edge(

            "MAIN",

            node_id,

            label=f"#{idx + 1}",

            width=3
        )

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".html"
    ) as tmp:

        net.save_graph(tmp.name)

        with open(
            tmp.name,
            "r",
            encoding="utf-8"
        ) as f:

            html_content = f.read()

    return html_content

# -------------------------
# الواجهة الرئيسية
# -------------------------
DATA_FILE = (
    "final_ontology_refined_"
    "mappings_with_explanations.csv"
)

if os.path.exists(DATA_FILE):

    df = pd.read_csv(DATA_FILE)

    df.columns = [
        c.strip()
        for c in df.columns
    ]

    st.title(
        "Control Mapping Viewer"
    )

    # ---------------------------------
    # قائمة الكنترولز
    # ---------------------------------
    control_list = df[
        "ECC id control"
    ].dropna().unique()

    selected_control = st.radio(
        "Control List",
        control_list
    )

    # ---------------------------------
    # الكنترول المختار
    # ---------------------------------
    selected_row = df[
        df["ECC id control"]
        == selected_control
    ].iloc[0]

    mappings = extract_mappings(
        selected_row,
        df
    )

    # ---------------------------------
    # تقسيم الشاشة
    # ---------------------------------
    left_col, right_col = st.columns(
        [2, 1]
    )

    # ---------------------------------
    # الجراف
    # ---------------------------------
    with left_col:

        graph_html = create_graph(

            selected_control,

            str(
                selected_row[
                    "Source Text"
                ]
            ),

            mappings
        )

        components.html(
            graph_html,
            height=780
        )

    # ---------------------------------
    # الشرح
    # ---------------------------------
    with right_col:

        st.markdown(
            "## AI Explanations"
        )

        if mappings:

            for idx, m in enumerate(mappings):

                with st.expander(
                    f"#{idx + 1} - "
                    f"{m['mapping']}"
                ):

                    st.markdown(
                        f"**Commonality:** "
                        f"{m['commonality']}"
                    )

                    st.markdown(
                        f"**Justification:** "
                        f"{m['justification']}"
                    )

                    st.markdown(
                        f"**Differences:** "
                        f"{m['differences']}"
                    )

        else:

            st.info(
                "No mappings found "
                "for this control."
            )

else:

    st.error(
        "Data file not found. "
        "Please ensure the CSV "
        "is in the same directory."
    )
