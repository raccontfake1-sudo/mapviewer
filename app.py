import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

# ---------------------------------
# إعداد الصفحة
# ---------------------------------
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
# استخراج المابات
# ---------------------------------
def extract_mappings(row, df, top_k=10):

    results = []

    for i in range(1, 11):

        cols = get_mapping_columns(i)

        if cols["mapping"] not in df.columns:
            continue

        if pd.isna(row.get(cols["mapping"])):
            continue

        try:

            val = str(
                row.get(cols["final"], 0)
            ).replace("%", "")

            score = float(val)

            if score > 1:
                score = score / 100.0

        except:
            score = 0.0

        results.append({

            "rank": i,

            "mapping": str(
                row.get(cols["mapping"], "")
            ),

            "text": str(
                row.get(cols["text"], "")
            ),

            "final": score,

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

# ---------------------------------
# رسم الجراف
# ---------------------------------
def create_graph(
    selected_id,
    source_text,
    mappings
):

    net = Network(
        height="700px",
        width="100%",
        bgcolor="#ffffff"
    )

    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -120,
          "springLength": 220
        },

        "solver": "forceAtlas2Based",

        "stabilization": {
          "iterations": 1000
        }
      },

      "nodes": {
        "borderWidth": 2,

        "font": {
          "size": 18,
          "face": "arial"
        }
      },

      "edges": {
        "smooth": {
          "type": "dynamic"
        },

        "font": {
          "size": 18,
          "align": "middle",
          "color": "#1476d4"
        },

        "color": "#d3dbe3"
      }
    }
    """)

    # العقدة الرئيسية الزرقاء
    net.add_node(
        "MAIN",

        label=str(selected_id),

        title=html.escape(
            source_text
        ),

        color="#1687d9",

        size=60,

        shape="dot",

        font={
            "color": "white",
            "size": 24
        }
    )

    # العقد الخضراء
    for item in mappings:

        node_id = (
            f"{item['mapping']}_{item['rank']}"
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

        # الأرقام مرتبة 1-10
        net.add_edge(
            "MAIN",

            node_id,

            label=str(item["rank"]),

            width=max(
                2,
                12 - item["rank"]
            )
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

# ---------------------------------
# الملف
# ---------------------------------
DATA_FILE = (
    "final_ontology_refined_"
    "mappings_with_explanations.csv"
)

# ---------------------------------
# تشغيل البرنامج
# ---------------------------------
if os.path.exists(DATA_FILE):

    df = pd.read_csv(DATA_FILE)

    df.columns = [
        c.strip()
        for c in df.columns
    ]

    st.title(
        "Control Mapping Viewer"
    )

    # ليست الكنترولز بدون بحث
    control_list = df[
        "ECC id control"
    ].dropna().unique()

    selected_control = st.radio(
        "Controls List",
        control_list
    )

    # الكنترول المختار
    selected_row = df[
        df["ECC id control"]
        == selected_control
    ].iloc[0]

    mappings = extract_mappings(
        selected_row,
        df
    )

    # تقسيم الشاشة
    left_col, right_col = st.columns(
        [2, 1]
    )

    # الجراف يسار
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
            height=750
        )

    # الشرح يمين
    with right_col:

        st.markdown(
            "## AI Explanations"
        )

        if mappings:

            for item in mappings:

                st.markdown(
                    f"### #{item['rank']} "
                    f"{item['mapping']}"
                )

                st.markdown(
                    f"**Commonality:** "
                    f"{item['commonality']}"
                )

                st.markdown(
                    f"**Justification:** "
                    f"{item['justification']}"
                )

                st.markdown(
                    f"**Differences:** "
                    f"{item['differences']}"
                )

                st.divider()

        else:

            st.info(
                "No mappings found."
            )

else:

    st.error(
        "Data file not found."
    )
