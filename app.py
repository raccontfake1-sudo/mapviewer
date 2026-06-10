import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os
import math
import json
import html
import re
import time

st.set_page_config(page_title="ECC-NIST Control Mapping Viewer", layout="wide")

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {
            background: #0f172a;
        }

        section[data-testid="stSidebar"] * {
            color: #e2e8f0 !important;
        }

        section[data-testid="stSidebar"] h1 {
            font-size: 18px !important;
            font-weight: 700 !important;
            color: #f8fafc !important;
            letter-spacing: 0.3px;
            padding-bottom: 4px;
            border-bottom: 1px solid #1e293b;
            margin-bottom: 12px !important;
        }

        /* Search box */
        section[data-testid="stSidebar"] input[type="text"] {
            background: #1e293b !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
            color: #f1f5f9 !important;
            font-size: 13px !important;
            padding: 8px 12px !important;
        }

        section[data-testid="stSidebar"] input[type="text"]::placeholder {
            color: #64748b !important;
        }

        /* Radio group */
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            gap: 0 !important;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: 6px 10px !important;
            margin: 1px 0 !important;
            border-radius: 6px !important;
            transition: background 0.15s ease !important;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: #1e293b !important;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label div,
        section[data-testid="stSidebar"] div[role="radiogroup"] label p,
        section[data-testid="stSidebar"] div[role="radiogroup"] label span {
            font-size: 13px !important;
            font-weight: 500 !important;
            line-height: 1.4 !important;
            color: #cbd5e1 !important;
        }

        section[data-testid="stSidebar"] .stRadio > label,
        section[data-testid="stSidebar"] .stRadio > label p {
            font-size: 11px !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
            color: #64748b !important;
            margin-bottom: 6px !important;
        }

        /* Main area */
        .main .block-container {
            padding-top: 24px !important;
            padding-bottom: 24px !important;
        }

        /* Streamlit download button */
        .stDownloadButton button {
            background: #1d4ed8 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            padding: 10px 22px !important;
            transition: background 0.2s ease !important;
        }

        .stDownloadButton button:hover {
            background: #1e40af !important;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Slider */
        .stSlider > div > div > div {
            background: #1d4ed8 !important;
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
        "embedding": f"Dense{suffix}",
        "ontology": f"Ontology Score{suffix}",
        "commonality": f"Commonality{suffix}",
        "justification": f"Justification{suffix}",
        "differences": f"Differences{suffix}"
    }


def find_col(df_columns, target):
    def normalise(s):
        return re.sub(r"[\s_]+", "", s).lower()

    target_norm = normalise(target)
    for col in df_columns:
        if normalise(col) == target_norm:
            return col
    return None


def safe_get_score(row, df_columns, col_name):
    actual = find_col(df_columns, col_name)
    if actual is None:
        return 0.0
    return parse_score(row.get(actual, 0))


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
    mapping = str(mapping).strip()
    if ":" in mapping:
        code, name = mapping.split(":", 1)
        code = code.strip()
        name = name.strip()
        if len(name) > 12:
            name = name[:11] + "…"
        return code, name
    parts = re.split(r"[-]", mapping)
    if len(parts) >= 2:
        number = "-".join(parts[:-1])
        name = parts[-1]
        if len(name) > 12:
            name = name[:11] + "…"
        return number, name
    if len(mapping) > 9:
        return mapping[:9], mapping[9:]
    return mapping, ""


def extract_mappings(row, df, top_k=5):
    results = []
    df_cols = list(df.columns)

    for i in range(1, 11):
        cols = get_mapping_columns(i)
        actual_mapping_col = find_col(df_cols, cols["mapping"])
        if actual_mapping_col is None:
            continue
        val = row.get(actual_mapping_col)
        if pd.isna(val) or str(val).strip() == "":
            continue

        final_score     = safe_get_score(row, df_cols, cols["final"])
        embedding_score = safe_get_score(row, df_cols, cols["embedding"])
        ontology_score  = safe_get_score(row, df_cols, cols["ontology"])

        actual_text = find_col(df_cols, cols["text"])
        actual_comm = find_col(df_cols, cols["commonality"])
        actual_just = find_col(df_cols, cols["justification"])
        actual_diff = find_col(df_cols, cols["differences"])

        raw_mapping = safe_value(row.get(actual_mapping_col, ""))
        code, name = short_mapping_label(raw_mapping)

        results.append({
            "mapping":       raw_mapping,
            "short_code":    code,
            "short_name":    name,
            "text":          safe_value(row.get(actual_text, "") if actual_text else ""),
            "final":         final_score,
            "embedding":     embedding_score,
            "ontology":      ontology_score,
            "commonality":   safe_value(row.get(actual_comm, "") if actual_comm else ""),
            "justification": safe_value(row.get(actual_just, "") if actual_just else ""),
            "differences":   safe_value(
                row.get(actual_diff, "") if actual_diff else "",
                "The controls differ in implementation focus and specific requirements."
            )
        })

    results = sorted(results, key=lambda x: x["final"], reverse=True)
    return results[:top_k]


# -------------------------
# SVG Viewer
# -------------------------
def create_svg_viewer(selected_id, source_text, mappings):
    width  = 620
    height = 420

    center_x = 310
    center_y = 210

    blue_radius  = 45
    green_radius = 38
    graph_radius = 155

    mapping_data = {}
    svg_lines  = ""
    svg_nodes  = ""
    svg_numbers = ""

    n = len(mappings)

    for idx, item in enumerate(mappings):
        angle = (2 * math.pi / n) * idx - (math.pi / 2)
        x = center_x + graph_radius * math.cos(angle)
        y = center_y + graph_radius * math.sin(angle)

        rank    = idx + 1
        node_id = f"node_{rank}"

        mapping_data[node_id] = {
            "rank":            str(rank),
            "ecc_control":     str(selected_id),
            "ecc_text":        source_text,
            "nist_control":    item["mapping"],
            "nist_short_code": item["short_code"],
            "nist_short_name": item["short_name"],
            "nist_text":       item["text"],
            "final":           format_decimal(item["final"]),
            "final_percent":   format_percent(item["final"]),
            "embedding":       format_decimal(item["embedding"]),
            "embedding_percent": format_percent(item["embedding"]),
            "ontology":        format_decimal(item["ontology"]),
            "ontology_percent": format_percent(item["ontology"]),
            "commonality":     item["commonality"],
            "justification":   item["justification"],
            "differences":     item["differences"]
        }

        dx = x - center_x
        dy = y - center_y
        distance = math.sqrt(dx * dx + dy * dy)

        start_x = center_x + (blue_radius  / distance) * dx
        start_y = center_y + (blue_radius  / distance) * dy
        end_x   = x        - (green_radius / distance) * dx
        end_y   = y        - (green_radius / distance) * dy

        svg_lines += f"""
            <line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}"
                  stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="4,3"/>
        """

        svg_numbers += f"""
            <text x="{x}" y="{y - green_radius - 10}"
                  text-anchor="middle" dominant-baseline="middle"
                  class="number-label">{rank}</text>
        """

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
                <circle cx="{x}" cy="{y}" r="{green_radius}" fill="#059669"/>
                {label_svg}
            </g>
        """

    mapping_json  = json.dumps(mapping_data, ensure_ascii=False)
    summary_rows_js = json.dumps([
        {
            "rank":          str(i + 1),
            "nist_control":  m["mapping"],
            "final_percent": format_percent(m["final"]),
            "final":         format_decimal(m["final"]),
        }
        for i, m in enumerate(mappings)
    ])

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}

            body {{
                font-family: 'Inter', Arial, sans-serif;
                background: #f8fafc;
                color: #1e293b;
            }}

            .main-card {{
                width: 100%;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                overflow: hidden;
                background: white;
                display: flex;
                flex-direction: column;
                box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);
            }}

            .top-row {{
                display: flex;
                height: 520px;
            }}

            .graph-section {{
                width: 65%;
                height: 520px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f8fafc;
                border-right: 1px solid #e2e8f0;
                position: relative;
            }}

            .graph-label {{
                position: absolute;
                top: 14px;
                left: 18px;
                font-size: 11px;
                font-weight: 600;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 0.7px;
            }}

            .summary-section {{
                width: 35%;
                height: 520px;
                padding: 20px;
                overflow-y: auto;
                background: white;
            }}

            .results-summary {{
                border-top: 1px solid #e2e8f0;
                padding: 16px 20px;
                background: #f8fafc;
            }}

            .results-summary-title {{
                font-size: 13px;
                font-weight: 600;
                color: #374151;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 6px;
            }}

            .results-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
            }}

            .results-table th {{
                background: #f1f5f9;
                color: #475569;
                padding: 8px 12px;
                text-align: left;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid #e2e8f0;
            }}

            .results-table td {{
                padding: 9px 12px;
                border-bottom: 1px solid #f1f5f9;
                color: #374151;
                vertical-align: middle;
            }}

            .results-table tr:last-child td {{ border-bottom: none; }}

            .results-table tr:hover td {{
                background: #eff6ff;
                cursor: pointer;
            }}

            .rank-badge {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: #1d4ed8;
                color: white;
                border-radius: 50%;
                width: 22px;
                height: 22px;
                font-weight: 700;
                font-size: 11px;
            }}

            .score-pill {{
                display: inline-block;
                background: #dcfce7;
                color: #166534;
                border: 1px solid #bbf7d0;
                border-radius: 20px;
                padding: 2px 10px;
                font-weight: 600;
                font-size: 12px;
            }}

            .mapping-node {{ cursor: pointer; }}
            .mapping-node circle {{
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15));
                transition: all 0.2s ease;
            }}
            .mapping-node:hover circle {{
                fill: #047857;
                filter: drop-shadow(0 3px 8px rgba(5,150,105,0.4));
            }}

            .green-label-code {{
                fill: white;
                font-size: 10.5px;
                font-weight: 700;
                pointer-events: none;
                font-family: 'Inter', Arial, sans-serif;
            }}

            .green-label-name {{
                fill: #a7f3d0;
                font-size: 9px;
                pointer-events: none;
                font-family: 'Inter', Arial, sans-serif;
            }}

            .blue-label {{
                fill: white;
                font-size: 16px;
                font-weight: 700;
                pointer-events: none;
                font-family: 'Inter', Arial, sans-serif;
            }}

            .number-label {{
                fill: #1d4ed8;
                font-size: 11px;
                font-weight: 700;
                font-family: 'Inter', Arial, sans-serif;
            }}

            /* Panel */
            .panel-title {{
                font-size: 15px;
                font-weight: 700;
                color: #0f172a;
                margin-bottom: 14px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e2e8f0;
            }}

            .sub-title {{
                font-size: 11px;
                font-weight: 600;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.6px;
                margin-top: 14px;
                margin-bottom: 6px;
            }}

            .content-box {{
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 12.5px;
                line-height: 1.6;
                color: #374151;
                background: #f8fafc;
                white-space: pre-wrap;
            }}

            .score-box {{
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                overflow: hidden;
            }}

            .score-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 12.5px;
                padding: 8px 12px;
                border-bottom: 1px solid #f1f5f9;
            }}

            .score-row:last-child {{ border-bottom: none; }}

            .score-label {{
                font-weight: 500;
                color: #64748b;
            }}

            .score-value {{
                font-weight: 600;
                color: #1d4ed8;
            }}

            .placeholder {{
                color: #94a3b8;
                font-size: 13px;
                line-height: 1.7;
                text-align: center;
                padding: 40px 16px;
                border: 1.5px dashed #e2e8f0;
                border-radius: 10px;
                margin-top: 8px;
            }}

            .placeholder-icon {{
                font-size: 28px;
                margin-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="main-card">
            <div class="top-row">
                <div class="graph-section">
                    <div class="graph-label">Control Mapping Graph</div>
                    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
                        {svg_lines}

                        <circle cx="{center_x}" cy="{center_y}" r="{blue_radius}"
                                fill="#1d4ed8"
                                filter="drop-shadow(0 3px 8px rgba(29,78,216,0.4))"/>

                        <text x="{center_x}" y="{center_y}"
                              text-anchor="middle" dominant-baseline="middle"
                              class="blue-label">{html.escape(str(selected_id))}</text>

                        {svg_nodes}
                        {svg_numbers}
                    </svg>
                </div>

                <div class="summary-section" id="summary-panel">
                    <div class="panel-title">Mapping Details</div>
                    <div class="placeholder">
                        <div class="placeholder-icon">🔗</div>
                        Click any green NIST control node to view detailed mapping information, scores, and analysis.
                    </div>
                </div>
            </div>

            <div class="results-summary">
                <div class="results-summary-title">
                    📋 Results Summary — {len(mappings)} mapping(s) for <b style="color:#1d4ed8; margin-left:4px;">{html.escape(str(selected_id))}</b>
                </div>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>NIST Control</th>
                            <th>Final Score</th>
                        </tr>
                    </thead>
                    <tbody id="summary-tbody"></tbody>
                </table>
            </div>
        </div>

        <script>
            const mappingData   = {mapping_json};
            const summaryRows   = {summary_rows_js};

            (function buildTable() {{
                const tbody = document.getElementById("summary-tbody");
                summaryRows.forEach(function(row) {{
                    const tr = document.createElement("tr");
                    tr.onclick = function() {{ updatePanel("node_" + row.rank); }};
                    tr.innerHTML = `
                        <td><span class="rank-badge">${{row.rank}}</span></td>
                        <td style="font-weight:500;">${{escapeHtml(row.nist_control)}}</td>
                        <td><span class="score-pill">${{escapeHtml(row.final_percent)}}</span></td>
                    `;
                    tbody.appendChild(tr);
                }});
            }})();

            function escapeHtml(text) {{
                if (!text) return "N/A";
                return String(text)
                    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
                    .replace(/>/g,"&gt;").replace(/"/g,"&quot;")
                    .replace(/'/g,"&#039;");
            }}

            function updatePanel(nodeId) {{
                const item  = mappingData[nodeId];
                const panel = document.getElementById("summary-panel");
                if (!item) return;

                const finalVal = parseFloat(item.final);
                const matchLabel = finalVal >= 0.85 ? "🟢 High Match"
                                 : finalVal >= 0.70 ? "🟡 Medium Match"
                                 : "🔴 Low Match";

                const relLabel = finalVal >= 0.85 ? "Strong"
                               : finalVal >= 0.70 ? "Moderate"
                               : "Weak";

                const domain = item.nist_control.startsWith("GV") ? "Govern"
                             : item.nist_control.startsWith("ID") ? "Identify"
                             : item.nist_control.startsWith("PR") ? "Protect"
                             : item.nist_control.startsWith("DE") ? "Detect"
                             : item.nist_control.startsWith("RS") ? "Respond"
                             : item.nist_control.startsWith("RC") ? "Recover"
                             : "Unknown";

                panel.innerHTML = `
                    <div class="panel-title">Mapping #${{item.rank}} Details</div>

                    <div class="sub-title">ECC Control</div>
                    <div class="content-box">
                        <b>${{escapeHtml(item.ecc_control)}}</b><br><br>
                        ${{escapeHtml(item.ecc_text)}}
                    </div>

                    <div class="sub-title">NIST Control</div>
                    <div class="content-box">
                        <b>${{escapeHtml(item.nist_control)}}</b><br><br>
                        ${{escapeHtml(item.nist_text)}}
                    </div>

                    <div class="sub-title">Scores & Analysis</div>
                    <div class="score-box">
                        <div class="score-row">
                            <span class="score-label">Final Score</span>
                            <span class="score-value">${{escapeHtml(item.final)}} (${{escapeHtml(item.final_percent)}})</span>
                        </div>
                        <div class="score-row">
                            <span class="score-label">Confidence</span>
                            <span class="score-value">${{matchLabel}}</span>
                        </div>
                        <div class="score-row">
                            <span class="score-label">Relationship</span>
                            <span class="score-value">${{relLabel}} Match</span>
                        </div>
                        <div class="score-row">
                            <span class="score-label">Domain</span>
                            <span class="score-value">${{domain}}</span>
                        </div>
                        <div class="score-row">
                            <span class="score-label">Embedding Score</span>
                            <span class="score-value">${{escapeHtml(item.embedding)}} (${{escapeHtml(item.embedding_percent)}})</span>
                        </div>
                        <div class="score-row">
                            <span class="score-label">Ontology Score</span>
                            <span class="score-value">${{escapeHtml(item.ontology)}} (${{escapeHtml(item.ontology_percent)}})</span>
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

    st.sidebar.title("ECC Controls")

    # ── Search box ─────────────────────────────────────────────────────
    search_term = st.sidebar.text_input(
        "Search ECC Control",
        placeholder="e.g. 1-1 or PR.AA",
        key="search_term"
    )

    all_control_ids = sorted(
        df["ECC id control"].astype(str).unique(),
        key=natural_control_sort
    )

    # Filter the list based on the search term
    if search_term.strip():
        filtered_ids = [
            cid for cid in all_control_ids
            if search_term.strip().lower() in cid.lower()
        ]
    else:
        filtered_ids = all_control_ids

    if not filtered_ids:
        st.sidebar.warning("No controls match your search.")
        filtered_ids = all_control_ids  # fallback to full list

    # ── Auto-select: if search narrows to 1 exact match, jump to it ──
    # Use session_state to keep track of the selected control
    if "selected_id" not in st.session_state:
        st.session_state.selected_id = all_control_ids[0]

    # If search term exactly matches one control ID, auto-select it
    exact_match = next(
        (cid for cid in all_control_ids if cid.lower() == search_term.strip().lower()),
        None
    )
    if exact_match and exact_match != st.session_state.selected_id:
        st.session_state.selected_id = exact_match

    # Ensure selected_id is in filtered list for the radio
    if st.session_state.selected_id not in filtered_ids:
        radio_default_idx = 0
    else:
        radio_default_idx = filtered_ids.index(st.session_state.selected_id)

    selected_id = st.sidebar.radio(
        "Select Control ID",
        filtered_ids,
        index=radio_default_idx,
        format_func=lambda x: x
    )

    # Update session state when user clicks a radio button
    st.session_state.selected_id = selected_id

    # ── Debug expander ──────────────────────────────────────────────────
    with st.sidebar.expander("🔍 Debug: CSV columns"):
        st.write("**All columns in CSV:**")
        for c in df.columns:
            st.write(f"• `{c}`")
        row_debug = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
        st.write("---")
        st.write("**Score column lookup for mapping 1:**")
        for label, target in [
            ("Final Score",     "Final Score"),
            ("Embedding Score", "Embedding Score"),
            ("Ontology Score",  "Ontology Score"),
        ]:
            found = find_col(list(df.columns), target)
            if found:
                raw_val = row_debug.get(found, "N/A")
                st.success(f"✅ `{target}` → `{found}` = `{raw_val}`")
            else:
                st.error(f"❌ `{target}` → NOT FOUND")
        st.write("---")
        st.write("**Score column lookup for mapping 2:**")
        for label, target in [
            ("Final Score 2",     "Final Score 2"),
            ("Embedding Score 2", "Embedding Score 2"),
            ("Ontology Score 2",  "Ontology Score 2"),
        ]:
            found = find_col(list(df.columns), target)
            if found:
                raw_val = row_debug.get(found, "N/A")
                st.success(f"✅ `{target}` → `{found}` = `{raw_val}`")
            else:
                st.error(f"❌ `{target}` → NOT FOUND")

    # ── Main row ────────────────────────────────────────────────────────
    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    source_text_col = find_col(list(df.columns), "Source Text")
    source_text = safe_value(row.get(source_text_col, "") if source_text_col else "")

    # ── Header ──────────────────────────────────────────────────────────
    header_col1, header_col2 = st.columns([4, 1.4])

    with header_col1:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
                border-radius: 12px 0 0 12px;
                padding: 20px 28px;
                margin-bottom: 10px;
                min-height: 110px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="font-size:11px; font-weight:600; color:#60a5fa;
                            text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">
                    ECC–NIST Framework
                </div>
                <h1 style="margin:0; font-size:26px; color:#f8fafc;
                           font-family:'Inter',Arial,sans-serif; font-weight:700; line-height:1.2;">
                    Control Mapping Viewer
                </h1>
                <p style="margin-top:8px; color:#94a3b8; font-size:13px;
                          font-family:'Inter',Arial,sans-serif;">
                    Active control: <span style="color:#60a5fa; font-weight:600;">{selected_id}</span>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with header_col2:
        st.markdown(
            """
            <div style="
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 0 12px 12px 0;
                padding: 16px 18px;
                margin-bottom: 10px;
                min-height: 110px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <p style="margin:0 0 10px 0; font-weight:600; color:#374151;
                          font-size:13px; text-transform:uppercase;
                          letter-spacing:0.5px;">
                    Top-K Mappings
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        top_k = st.select_slider(
            "Top-K Recommendations",
            options=list(range(1, 6)),
            value=5,
            label_visibility="collapsed"
        )

    mappings = extract_mappings(row, df, top_k=top_k)

    st.markdown(
        f"""
        <div style="margin-top:-8px; margin-bottom:12px; color:#64748b; font-size:13px;">
            Showing <b style="color:#1d4ed8;">{len(mappings)}</b> recommended mapping(s) for
            <b style="color:#1d4ed8;">{selected_id}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    viewer_html = create_svg_viewer(
        selected_id=str(selected_id),
        source_text=source_text,
        mappings=mappings
    )

    col_graph, col_status = st.columns([4, 1])

    with col_status:
        st.markdown(
            """
            <div style="background:#0f172a; border-radius:10px; padding:16px 14px;
                        margin-bottom:8px;">
                <div style="font-size:11px; font-weight:600; color:#60a5fa;
                            text-transform:uppercase; letter-spacing:0.8px;
                            margin-bottom:10px;">
                    Processing Pipeline
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        pipeline_box = st.empty()

        steps = [
            "Loading ECC Control",
            "Loading NIST Controls",
            "Extracting Metadata",
            "Semantic Embeddings",
            "Ontology Scoring",
            "Confidence Matching",
            "AI Explanation",
            "Returning Top-K"
        ]

        step_icons = ["📁", "📚", "🔍", "🧠", "🌐", "📊", "✨", "✅"]

        completed = []
        for step in steps:
            completed.append(step)
            rows_html = ""
            for i, s in enumerate(steps):
                if s in completed:
                    rows_html += f'<div style="font-size:12px; color:#86efac; padding:3px 0;">✅ {s}</div>'
                else:
                    rows_html += f'<div style="font-size:12px; color:#475569; padding:3px 0;">⬜ {s}</div>'
            pipeline_box.markdown(
                f'<div style="background:#0f172a; border-radius:10px; padding:12px 14px;">{rows_html}</div>',
                unsafe_allow_html=True
            )
            time.sleep(0.15)

    with col_graph:
        components.html(viewer_html, height=700, scrolling=False)

    # ── Export ──────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="height:1px; background:#e2e8f0; margin:20px 0 16px 0;"></div>
        <div style="font-size:15px; font-weight:600; color:#1e293b; margin-bottom:10px;">
            Export Mapping Report
        </div>
        """,
        unsafe_allow_html=True
    )

    export_df = pd.DataFrame(mappings)
    csv = export_df.to_csv(index=False)

    st.download_button(
        label="⬇  Export CSV Report",
        data=csv,
        file_name=f"{selected_id}_mapping_report.csv",
        mime="text/csv"
    )

else:
    st.markdown(
        f"""
        <div style="
            background:#fef2f2; border:1px solid #fecaca;
            border-radius:10px; padding:24px; margin-top:30px;
        ">
            <div style="font-size:16px; font-weight:700; color:#991b1b; margin-bottom:8px;">
                ⚠️ Data file not found
            </div>
            <div style="color:#7f1d1d; font-size:14px;">
                Make sure <code>{DATA_FILE}</code> is in the same folder as <code>mapviewer.py</code>.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
