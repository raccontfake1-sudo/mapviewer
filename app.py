import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os
import math
import json

st.set_page_config(page_title="Control Mapping Viewer", layout="wide")


# -------------------------
# Mapping columns helper
# -------------------------
def get_mapping_columns(i):
    suffix = "" if i == 1 else f" {i}"
    return {
        "mapping": f"NIST mapping{suffix}",
        "text": f"Text{suffix}",
        "final": f"Final Score{suffix}",
        "embedding": f"Embedding Score{suffix}",
        "ontology": f"Ontology Score{suffix}",
        "commonality": f"Commonality{suffix}",
        "justification": f"Justification{suffix}",
        "differences": f"Differences{suffix}"
    }


def safe_value(value, default="N/A"):
    if pd.isna(value) or str(value).strip() == "":
        return default
    return str(value).strip()


def parse_score(value):
    try:
        if pd.isna(value):
            return 0.0

        value = str(value).replace("%", "").strip()

        if value == "":
            return 0.0

        value = float(value)

        if value > 1:
            return value / 100.0

        return value

    except:
        return 0.0


def format_score(score):
    try:
        return f"{float(score):.2f}"
    except:
        return "N/A"


def extract_mappings(row, df, top_k=10):
    results = []

    for i in range(1, 11):
        cols = get_mapping_columns(i)

        if cols["mapping"] not in df.columns or pd.isna(row.get(cols["mapping"])):
            continue

        final_score = parse_score(row.get(cols["final"], 0))

        embedding_score = parse_score(row.get(cols["embedding"], 0)) if cols["embedding"] in df.columns else 0.0
        ontology_score = parse_score(row.get(cols["ontology"], 0)) if cols["ontology"] in df.columns else 0.0

        differences_val = safe_value(
            row.get(cols["differences"], ""),
            "The controls differ in implementation focus and specific requirements."
        )

        results.append({
            "rank": i,
            "mapping": safe_value(row.get(cols["mapping"], "")),
            "text": safe_value(row.get(cols["text"], "")),
            "final": final_score,
            "embedding": embedding_score,
            "ontology": ontology_score,
            "commonality": safe_value(row.get(cols["commonality"], "")),
            "justification": safe_value(row.get(cols["justification"], "")),
            "differences": differences_val
        })

    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]


# -------------------------
# Create graph
# -------------------------
def create_graph(selected_id, source_text, mappings):

    net = Network(
        height="720px",
        width="100%",
        bgcolor="#ffffff",
        directed=False
    )

    net.set_options("""
    {
      "physics": {
        "enabled": false
      },
      "interaction": {
        "hover": true,
        "selectConnectedEdges": true
      },
      "nodes": {
        "borderWidth": 3,
        "font": {
          "size": 18,
          "face": "arial"
        }
      },
      "edges": {
        "color": "#7d8fa6",
        "font": {
          "size": 26,
          "align": "middle",
          "color": "#001f5c"
        },
        "smooth": {
          "enabled": true,
          "type": "continuous"
        }
      }
    }
    """)

    # Center ECC node
    net.add_node(
        selected_id,
        label=str(selected_id),
        title=html.escape(source_text),
        color="#1687d9",
        size=90,
        shape="circle",
        physics=False,
        font={"color": "white", "size": 34}
    )

    n = len(mappings)

    for idx, item in enumerate(mappings):

        angle = (2 * math.pi / n) * idx
        x = 520 * math.cos(angle)
        y = 520 * math.sin(angle)

        tooltip = f"""
        <b>NIST Control:</b> {html.escape(item["mapping"])}<br>
        <b>Final Score:</b> {format_score(item["final"])}<br>
        <b>Embedding Score:</b> {format_score(item["embedding"])}<br>
        <b>Ontology Score:</b> {format_score(item["ontology"])}<br><br>
        <b>Text:</b><br>{html.escape(item["text"])}
        """

        net.add_node(
            item["mapping"],
            label=f"{idx + 1}\\n{item['mapping']}\\nFinal: {format_score(item['final'])}",
            title=tooltip,
            color="#2e7d32",
            size=75,
            shape="circle",
            x=x,
            y=y,
            physics=False,
            font={"color": "white", "size": 16}
        )

        net.add_edge(
            selected_id,
            item["mapping"],
            label=str(idx + 1),
            color="#1f4e79",
            width=4
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)

        with open(tmp.name, "r", encoding="utf-8") as f:
            graph_html = f.read()

    mapping_data = {
        item["mapping"]: {
            "mapping": item["mapping"],
            "text": item["text"],
            "final": format_score(item["final"]),
            "embedding": format_score(item["embedding"]),
            "ontology": format_score(item["ontology"]),
            "commonality": item["commonality"],
            "justification": item["justification"],
            "differences": item["differences"]
        }
        for item in mappings
    }

    mapping_json = json.dumps(mapping_data, ensure_ascii=False)

    custom_panel = f"""
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}

        #main-container {{
            display: flex;
            width: 100%;
            height: 720px;
        }}

        #graph-container {{
            width: 70%;
            height: 720px;
            border-right: 1px solid #d9d9d9;
        }}

        #details-panel {{
            width: 30%;
            height: 720px;
            overflow-y: auto;
            padding: 24px;
            box-sizing: border-box;
            background-color: #f8fafc;
            border-left: 1px solid #d9d9d9;
        }}

        .panel-title {{
            font-size: 24px;
            font-weight: bold;
            color: #12355b;
            margin-bottom: 16px;
        }}

        .sub-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2e7d32;
            margin-top: 18px;
            margin-bottom: 8px;
        }}

        .score-box {{
            background-color: white;
            border: 1px solid #d0d7de;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 12px;
        }}

        .score-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 15px;
        }}

        .score-label {{
            font-weight: bold;
            color: #333333;
        }}

        .score-value {{
            color: #001f5c;
            font-weight: bold;
        }}

        .content-box {{
            background-color: white;
            border: 1px solid #d0d7de;
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 14px;
            line-height: 1.5;
            font-size: 15px;
            color: #222222;
        }}

        .placeholder {{
            color: #666666;
            font-size: 16px;
            line-height: 1.6;
        }}
    </style>

    <script>
        const mappingData = {mapping_json};

        function escapeHtml(text) {{
            if (!text) return "N/A";
            return String(text)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }}

        function updatePanel(nodeId) {{
            const panel = document.getElementById("details-panel");

            if (!mappingData[nodeId]) {{
                panel.innerHTML = `
                    <div class="panel-title">AI Explanations</div>
                    <div class="placeholder">
                        Click on a green NIST mapping circle to view its explanation, final score, embedding score, and ontology score.
                    </div>
                `;
                return;
            }}

            const item = mappingData[nodeId];

            panel.innerHTML = `
                <div class="panel-title">AI Explanation</div>

                <div class="sub-title">Selected NIST Mapping</div>
                <div class="content-box">${{escapeHtml(item.mapping)}}</div>

                <div class="sub-title">Scores</div>
                <div class="score-box">
                    <div class="score-row">
                        <span class="score-label">Final Score</span>
                        <span class="score-value">${{escapeHtml(item.final)}}</span>
                    </div>
                    <div class="score-row">
                        <span class="score-label">Embedding Score</span>
                        <span class="score-value">${{escapeHtml(item.embedding)}}</span>
                    </div>
                    <div class="score-row">
                        <span class="score-label">Ontology Score</span>
                        <span class="score-value">${{escapeHtml(item.ontology)}}</span>
                    </div>
                </div>

                <div class="sub-title">Mapped Control Text</div>
                <div class="content-box">${{escapeHtml(item.text)}}</div>

                <div class="sub-title">Commonality</div>
                <div class="content-box">${{escapeHtml(item.commonality)}}</div>

                <div class="sub-title">Justification</div>
                <div class="content-box">${{escapeHtml(item.justification)}}</div>

                <div class="sub-title">Differences</div>
                <div class="content-box">${{escapeHtml(item.differences)}}</div>
            `;
        }}
    </script>
    """

    graph_html = graph_html.replace(
        '<body>',
        '<body>' + custom_panel + '<div id="main-container"><div id="graph-container">'
    )

    graph_html = graph_html.replace(
        '</body>',
        '''
        </div>
        <div id="details-panel">
            <div class="panel-title">AI Explanations</div>
            <div class="placeholder">
                Click on a green NIST mapping circle to view its explanation, final score, embedding score, and ontology score.
            </div>
        </div>
        </div>

        <script>
            network.on("click", function(params) {
                if (params.nodes.length > 0) {
                    const selectedNode = params.nodes[0];
                    updatePanel(selectedNode);
                }
            });
        </script>
        </body>
        '''
    )

    return graph_html


# -------------------------
# Load data
# -------------------------
DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):

    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    st.sidebar.title("Controls")

    control_ids = sorted(df["ECC id control"].astype(str).unique())

    selected_id = st.sidebar.radio("Select Control ID", control_ids)

    st.title("Control Mapping Viewer")

    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]

    source_text = safe_value(row.get("Source Text", ""))

    mappings = extract_mappings(row, df)

    graph_html = create_graph(
        str(selected_id),
        source_text,
        mappings
    )

    components.html(graph_html, height=750, scrolling=True)

else:
    st.error("CSV file not found")
