import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

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

        commonality_val = row.get(
            cols["commonality"],
            ""
        )

        justification_val = row.get(
            cols["justification"],
            ""
        )

        differences_val = row.get(
            cols["differences"],
            ""
        )

        if pd.isna(differences_val) or differences_val == "":
            differences_val = (
                "The controls differ in "
                "implementation focus and "
                "specific requirements."
            )

        results.append({
            "mapping": str(
                row.get(cols["mapping"], "")
            ),

            "text": str(
                row.get(cols["text"], "")
            ),

            "final": score,

            "commonality": (
                str(commonality_val)
                if not pd.isna(commonality_val)
                else "N/A"
            ),

            "justification": (
                str(justification_val)
                if not pd.isna(justification_val)
                else "N/A"
            ),

            "differences": str(
                differences_val
            )
        })

    results = sorted(
        results,
        key=lambda x: x["final"],
        reverse=True
    )

    return results[:top_k]

# -------------------------
# رسم الـ Graph
# -------------------------
def create_graph(
    selected_id,
    source_text,
    mappings
):

    net = Network(
        height="850px",
        width="100%",
        bgcolor="#ffffff"
    )

    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -100,
          "springLength": 180
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
        "smooth": false,

        "font": {
          "size": 16,
          "align": "middle",
          "color": "#1476d4"
        },

        "color": "#d3dbe3"
      }
    }
    """)

    # العقدة الرئيسية الزرقاء
    net.add_node(
        selected_id,
        label=str(selected_id),
        title=html.escape(source_text),
        color="#1687d9",
        size=55,
        shape="dot",

        font={
            "color": "white",
            "size": 24
        }
    )

    # الكنترولز الخضراء
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

            size=32,

            shape="circle",

            font={
                "color": "white"
            }
        )

        # الهاشتاقات
        net.add_edge(
            selected_id,
            node_id,

            label=f"#{idx + 1}",

            width=max(
                1,
                10 - idx
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

    for _, row in df.iterrows():

        selected_id = row[
            "ECC id control"
        ]

        mappings = extract_mappings(
            row,
            df
        )

        graph_html = create_graph(
            selected_id,
            str(row["Source Text"]),
            mappings
        )

        components.html(
            graph_html,
            height=900
        )

        st.divider()

        st.markdown(
            "## AI Explanations"
        )

        if mappings:

            for idx, m in enumerate(
                mappings
            ):

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

                    st.divider()

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
