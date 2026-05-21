import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os
import math
import json
import html
import re

st.set_page_config(page_title="NCA-NIST Control Mapping Viewer", layout="wide")

st.markdown(
    """
    <style>
        /* ── Nuclear option: force every text node inside sidebar radio ── */

        /* The wrapper div */
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            gap: 0 !important;
        }

        /* Each radio row label */
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: 4px 8px !important;
            margin: 0 !important;
            min-height: unset !important;
        }

        /* The visible text span — this is what actually renders the ID */
        section[data-testid="stSidebar"] div[role="radiogroup"] label div,
        section[data-testid="stSidebar"] div[role="radiogroup"] label p,
        section[data-testid="stSidebar"] div[role="radiogroup"] label span {
            font-size: 28px !important;
            font-weight: 800 !important;
            line-height: 1.2 !important;
            letter-spacing: 0.5px !important;
        }

        /* "Select Control ID" group label */
        section[data-testid="stSidebar"] .stRadio > label,
        section[data-testid="stSidebar"] .stRadio > label p {
            font-size: 15px !important;
            font-weight: bold !important;
            display: block !important;
        }

        /* Sidebar title */
        section[data-testid="stSidebar"] h1 {
            font-size: 26px !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# -------------------------
# Helpers
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


def natural_control_sort(value):
    value = str(value).strip()
    parts = re.split(r"[.\-_\s]+", value)

    sort_key = []
    for part in parts:
        if part.isdigit():
            sort_key.append(int(part))
        else:
            sort_key.append(part)

    return sort_key


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


def format_decimal(score):
    try:
        return f"{float(score):.2f}"
    except:
        return "N/A"


def format_percent(score):
    try:
        return f"{int(round(float(score) * 100))}%"
    except:
        return "N/A"


def short_mapping_label(mapping):
    """
    Returns a two-line label: number part on line 1, name part on line 2.
    E.g. 'GV.SC-1: Governance' → ('GV.SC-1', 'Governance')
    If no colon, split at the dot or just return the raw value.
    """
    mapping = str(mapping).strip()

    if ":" in mapping:
        code, name = mapping.split(":", 1)
        code = code.strip()
        name = name.strip()
        # Truncate name if too long
        if len(name) > 12:
            name = name[:11] + "…"
        return code, name

    # No colon — try splitting on last dash as number / family
    parts = re.split(r"[-]", mapping)
    if len(parts) >= 2:
        number = "-".join(parts[:-1])
        name = parts[-1]
        if len(name) > 12:
            name = name[:11] + "…"
        return number, name

    # Fallback: split at 9 chars
    if len(mapping) > 9:
        return mapping[:9], mapping[9:]
    return mapping, ""


def extract_mappings(row, df, top_k=5):
    results = []

    for i in range(1, 11):
        cols = get_mapping_columns(i)

        if cols["mapping"] not in df.columns:
            continue

        if pd.isna(row.get(cols["mapping"])):
            continue

        final_score = parse_score(row.get(cols["final"], 0))

        embedding_score = (
            parse_score(row.get(cols["embedding"], 0))
            if cols["embedding"] in df.columns
            else 0.0
        )

        ontology_score = (
            parse_score(row.get(cols["ontology"], 0))
            if cols["ontology"] in df.columns
            else 0.0
        )

        raw_mapping = safe_value(row.get(cols["mapping"], ""))
        code, name = short_mapping_label(raw_mapping)

        results.append({
            "mapping": raw_mapping,
            "short_code": code,
            "short_name": name,
            "text": safe_value(row.get(cols["text"], "")),
            "final": final_score,
            "embedding": embedding_score,
            "ontology": ontology_score,
            "commonality": safe_value(row.get(cols["commonality"], "")),
            "justification": safe_value(row.get(cols["justification"], "")),
            "differences": safe_value(
                row.get(cols["differences"], ""),
                "The controls differ in implementation focus and specific requirements."
            )
        })

    results = sorted(results, key=lambda x: x["final"], reverse=True)
    return results[:top_k]


# -------------------------
# SVG Viewer
# -------------------------
def create_svg_viewer(selected_id, source_text, mappings):

    width = 620
    height = 420

    center_x = 310
    center_y = 210

    blue_radius = 45
    green_radius = 38   # slightly larger to fit two lines
    graph_radius = 155

    mapping_data = {}

    svg_lines = ""
    svg_nodes = ""
    svg_numbers = ""

    n = len(mappings)

    for idx, item in enumerate(mappings):
        angle = (2 * math.pi / n) * idx - (math.pi / 2)

        x = center_x + graph_radius * math.cos(angle)
        y = center_y + graph_radius * math.sin(angle)

        rank = idx + 1
        node_id = f"node_{rank}"

        mapping_data[node_id] = {
            "rank": str(rank),
            "ecc_control": str(selected_id),
            "ecc_text": source_text,
            "nist_control": item["mapping"],
            "nist_short_code": item["short_code"],
            "nist_short_name": item["short_name"],
            "nist_text": item["text"],
            "final": format_decimal(item["final"]),
            "final_percent": format_percent(item["final"]),
            "embedding": format_decimal(item["embedding"]),
            "embedding_percent": format_percent(item["embedding"]),
            "ontology": format_decimal(item["ontology score"]),
            "ontology_percent": format_percent(item["ontology"]),
            "commonality": item["commonality"],
            "justification": item["justification"],
            "differences": item["differences"]
        }

        dx = x - center_x
        dy = y - center_y
        distance = math.sqrt(dx * dx + dy * dy)

        start_x = center_x + (blue_radius / distance) * dx
        start_y = center_y + (blue_radius / distance) * dy

        end_x = x - (green_radius / distance) * dx
        end_y = y - (green_radius / distance) * dy

        svg_lines += f"""
            <line 
                x1="{start_x}" 
                y1="{start_y}" 
                x2="{end_x}" 
                y2="{end_y}" 
                stroke="#b8c4d0" 
                stroke-width="2"
            />
        """

        svg_numbers += f"""
            <text 
                x="{x}" 
                y="{y - green_radius - 10}" 
                text-anchor="middle" 
                dominant-baseline="middle"
                class="number-label"
            >
                {rank}
            </text>
        """

        # Two-line label: code on top, name below
        code_escaped = html.escape(item["short_code"])
        name_escaped = html.escape(item["short_name"])

        if name_escaped:
            label_svg = f"""
                <text x="{x}" y="{y - 7}" text-anchor="middle" dominant-baseline="middle" class="green-label-code">{code_escaped}</text>
                <text x="{x}" y="{y + 10}" text-anchor="middle" dominant-baseline="middle" class="green-label-name">{name_escaped}</text>
            """
        else:
            label_svg = f"""
                <text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" class="green-label-code">{code_escaped}</text>
            """

        svg_nodes += f"""
            <g class="mapping-node" onclick="updatePanel('{node_id}')">
                <circle 
                    cx="{x}" 
                    cy="{y}" 
                    r="{green_radius}" 
                    fill="#2f9b4f"
                />
                {label_svg}
            </g>
        """

    mapping_json = json.dumps(mapping_data, ensure_ascii=False)

    # Build summary rows for the summary section
    summary_rows_js = json.dumps([
        {
            "rank": str(i + 1),
            "nist_control": m["mapping"],
            "final_percent": format_percent(m["final"]),
            "final": format_decimal(m["final"]),
        }
        for i, m in enumerate(mappings)
    ])

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background: #ffffff;
            }}

            .main-card {{
                width: 100%;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                overflow: hidden;
                background: white;
                display: flex;
                flex-direction: column;
            }}

            .top-row {{
                display: flex;
                height: 520px;
            }}

            .graph-section {{
                width: 68%;
                height: 520px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: white;
            }}

            .summary-section {{
                width: 32%;
                height: 520px;
                border-left: 1px solid #e0e0e0;
                padding: 22px;
                box-sizing: border-box;
                overflow-y: auto;
                background: #ffffff;
            }}

            /* ---- Results Summary Strip ---- */
            .results-summary {{
                border-top: 1px solid #e0e0e0;
                padding: 16px 24px;
                background: #f8fafc;
            }}

            .results-summary-title {{
                font-size: 14px;
                font-weight: bold;
                color: #1f2933;
                margin-bottom: 10px;
            }}

            .results-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
            }}

            .results-table th {{
                background: #e8eef5;
                color: #1f2933;
                padding: 6px 10px;
                text-align: left;
                font-weight: bold;
                border-bottom: 1px solid #d0d7de;
            }}

            .results-table td {{
                padding: 6px 10px;
                border-bottom: 1px solid #e8eef5;
                color: #333;
                vertical-align: top;
            }}

            .results-table tr:last-child td {{
                border-bottom: none;
            }}

            .results-table tr:hover td {{
                background: #eef4fb;
                cursor: pointer;
            }}

            .rank-badge {{
                display: inline-block;
                background: #0b72d9;
                color: white;
                border-radius: 50%;
                width: 22px;
                height: 22px;
                text-align: center;
                line-height: 22px;
                font-weight: bold;
                font-size: 12px;
            }}

            .score-pill {{
                display: inline-block;
                background: #2f9b4f;
                color: white;
                border-radius: 12px;
                padding: 2px 9px;
                font-weight: bold;
                font-size: 12px;
            }}

            .mapping-node {{
                cursor: pointer;
            }}

            .mapping-node:hover circle {{
                fill: #238442;
            }}

            .green-label-code {{
                fill: white;
                font-size: 11px;
                font-weight: bold;
                pointer-events: none;
            }}

            .green-label-name {{
                fill: #d4f5e2;
                font-size: 9.5px;
                pointer-events: none;
            }}

            .blue-label {{
                fill: white;
                font-size: 18px;
                font-weight: bold;
                pointer-events: none;
            }}

            .number-label {{
                fill: #3366cc;
                font-size: 13px;
                font-weight: bold;
            }}

            .panel-title {{
                font-size: 20px;
                font-weight: bold;
                color: #1f2933;
                margin-bottom: 16px;
            }}

            .sub-title {{
                font-size: 14px;
                font-weight: bold;
                color: #1f2933;
                margin-top: 16px;
                margin-bottom: 6px;
            }}

            .content-box {{
                border: 1px solid #d0d7de;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                line-height: 1.5;
                color: #222;
                margin-bottom: 10px;
                white-space: pre-wrap;
                background: #ffffff;
            }}

            .score-box {{
                border: 1px solid #d0d7de;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;
                background: #ffffff;
            }}

            .score-row {{
                display: flex;
                justify-content: space-between;
                font-size: 13px;
                margin-bottom: 7px;
            }}

            .score-label {{
                font-weight: bold;
                color: #333;
            }}

            .score-value {{
                font-weight: bold;
                color: #0b72d9;
            }}

            .placeholder {{
                color: #666;
                font-size: 14px;
                line-height: 1.6;
            }}
        </style>
    </head>

    <body>
        <div class="main-card">

            <div class="top-row">
                <div class="graph-section">
                    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">

                        {svg_lines}

                        <circle 
                            cx="{center_x}" 
                            cy="{center_y}" 
                            r="{blue_radius}" 
                            fill="#0b72d9"
                        />

                        <text 
                            x="{center_x}" 
                            y="{center_y}" 
                            text-anchor="middle" 
                            dominant-baseline="middle"
                            class="blue-label"
                        >
                            {html.escape(str(selected_id))}
                        </text>

                        {svg_nodes}

                        {svg_numbers}

                    </svg>
                </div>

                <div class="summary-section" id="summary-panel">
                    <div class="panel-title">Mapping Summary</div>
                    <div class="placeholder">
                        Click on a green NIST control circle to view the ECC control, NIST control, scores, commonality, justification, and differences.
                    </div>
                </div>
            </div>

            <!-- Results Summary Strip -->
            <div class="results-summary">
                <div class="results-summary-title">Results Summary — {len(mappings)} Mapping(s) for <b>{html.escape(str(selected_id))}</b></div>
                <table class="results-table" id="summary-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>NIST Control</th>
                            <th>Final Score</th>
                        </tr>
                    </thead>
                    <tbody id="summary-tbody">
                    </tbody>
                </table>
            </div>

        </div>

        <script>
            const mappingData = {mapping_json};
            const summaryRows = {summary_rows_js};

            // Populate summary table
            (function buildTable() {{
                const tbody = document.getElementById("summary-tbody");
                summaryRows.forEach(function(row, idx) {{
                    const tr = document.createElement("tr");
                    tr.onclick = function() {{ updatePanel("node_" + row.rank); }};
                    tr.innerHTML = `
                        <td><span class="rank-badge">${{row.rank}}</span></td>
                        <td>${{escapeHtml(row.nist_control)}}</td>
                        <td><span class="score-pill">${{escapeHtml(row.final_percent)}}</span></td>
                    `;
                    tbody.appendChild(tr);
                }});
            }})();

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
                const item = mappingData[nodeId];
                const panel = document.getElementById("summary-panel");

                if (!item) {{
                    return;
                }}

                panel.innerHTML = `
                    <div class="panel-title">Mapping Summary</div>

                    <div class="sub-title">Selected Mapping Number</div>
                    <div class="content-box">
                        <b>Number:</b> ${{escapeHtml(item.rank)}}
                    </div>

                    <div class="sub-title">ECC Mapping Control</div>
                    <div class="content-box">
                        <b>ECC Control:</b> ${{escapeHtml(item.ecc_control)}}<br><br>
                        <b>ECC Text:</b><br>${{escapeHtml(item.ecc_text)}}
                    </div>

                    <div class="sub-title">NIST Mapping Control</div>
                    <div class="content-box">
                        <b>NIST Control:</b> ${{escapeHtml(item.nist_control)}}<br><br>
                        <b>NIST Text:</b><br>${{escapeHtml(item.nist_text)}}
                    </div>

                    <div class="sub-title">Scores</div>
                    <div class="score-box">
                        <div class="score-row">
                            <span class="score-label">Final Score</span>
                            <span class="score-value">${{escapeHtml(item.final)}} / ${{escapeHtml(item.final_percent)}}</span>
                        </div>
                        <div class="score-row">
                            <span class="score-label">Embedding Score</span>
                            <span class="score-value">${{escapeHtml(item.embedding)}} / ${{escapeHtml(item.embedding_percent)}}</span>
                        </div>
                        <div class="score-row">
                            <span class="score-label">Ontology Score</span>
                            <span class="score-value">${{escapeHtml(item.ontology)}} / ${{escapeHtml(item.ontology_percent)}}</span>
                        </div>
                    </div>

                    <div class="sub-title">Commonality</div>
                    <div class="content-box">${{escapeHtml(item.commonality)}}</div>

                    <div class="sub-title">Justification</div>
                    <div class="content-box">${{escapeHtml(item.justification)}}</div>

                    <div class="sub-title">Differences</div>
                    <div class="content-box">${{escapeHtml(item.differences)}}</div>
                `;
            }}
        </script>
    </body>
    </html>
    """

    return html_code


# -------------------------
# Load data
# -------------------------
DATA_FILE = "final_with_explanations_COMPLETE.csv"

if os.path.exists(DATA_FILE):

    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    if "ECC id control" not in df.columns:
        st.error("Column 'ECC id control' was not found in the CSV file.")
        st.stop()

    st.sidebar.title("Controls")

    control_ids = sorted(
        df["ECC id control"].astype(str).unique(),
        key=natural_control_sort
    )

    selected_id = st.sidebar.radio(
        "Select Control ID",
        control_ids,
        format_func=lambda x: x
    )

    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    source_text = safe_value(row.get("Source Text", ""))

    # -------------------------
    # Header — number selector fills the right box better
    # -------------------------
    header_col1, header_col2 = st.columns([4, 1.2])

    with header_col1:
        st.markdown(
            f"""
            <div style="
                background-color:white;
                border:1px solid #e0e0e0;
                border-right:0;
                border-radius:10px 0 0 10px;
                padding:18px 24px;
                margin-bottom:10px;
                min-height:125px;
            ">
                <h1 style="margin:0; font-size:34px; color:#1f2933;">
                    NCA-NIST Control Mapping Viewer
                </h1>
                <p style="margin-top:28px;color:#4b5563;font-size:15px;">
                    Viewing mappings for: <b>{selected_id}</b>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with header_col2:
        st.markdown(
            """
            <div style="
                background-color:white;
                border:1px solid #e0e0e0;
                border-left:0;
                border-radius:0 10px 10px 0;
                padding:16px 18px 0 18px;
                margin-bottom:0;
                min-height:125px;
                display:flex;
                flex-direction:column;
                justify-content:center;
            ">
                <p style="margin:0 0 8px 0; font-weight:bold; color:#1f2933; font-size:16px;">
                    Number of circles
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ---- Counter 1–10 (select_slider gives a compact single-line picker) ----
        top_k = st.select_slider(
            "Number of circles",
            options=list(range(1, 11)),
            value=5,
            label_visibility="collapsed"
        )

    mappings = extract_mappings(row, df, top_k=top_k)

    st.markdown(
        f"""
        <div style="
            margin-top:-14px;
            margin-bottom:10px;
            color:#4b5563;
            font-size:15px;
        ">
            Showing <b>{len(mappings)}</b> recommended mapping(s).
        </div>
        """,
        unsafe_allow_html=True
    )

    viewer_html = create_svg_viewer(
        selected_id=str(selected_id),
        source_text=source_text,
        mappings=mappings
    )

    # Extra height to show the summary table below the graph
    components.html(viewer_html, height=700, scrolling=False)

else:
    st.error("CSV file not found. Make sure this file is in the same folder as mapviewer.py:")
    st.code(DATA_FILE)
