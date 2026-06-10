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

# Custom CSS with improvements
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        section[data-testid="stSidebar"] {
            background: #1e293b;
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
            border-bottom: 1px solid #334155;
            margin-bottom: 12px !important;
        }

        /* Sidebar inputs styling */
        section[data-testid="stSidebar"] input[type="text"] {
            background: #273549 !important;
            border: 1px solid #475569 !important;
            border-radius: 8px !important;
            color: #f1f5f9 !important;
            font-size: 13px !important;
            padding: 8px 12px !important;
        }

        /* Main container adjustments */
        .main .block-container {
            padding-top: 0px !important;
            padding-bottom: 24px !important;
        }

        /* Download button style */
        .stDownloadButton button {
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            padding: 10px 22px !important;
            transition: background 0.2s ease !important;
        }

        .stDownloadButton button:hover {
            background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
        }

        /* Scrollbar for summary panel */
        .summary-section {
            overflow-y: auto;
            max-height: 560px;
        }

        /* Graph, legend, control panel styles */
        /* ... (keep your existing style definitions, possibly cleaned up) ... */

        /* SVG nodes hover effect */
        .mapping-node:hover .glow-ring { opacity: 0.38 !important; }

        /* Dynamic number labels styling */
        .number-label {
            font-size: 10px; font-weight: 700;
            font-family: 'Inter', Arial, sans-serif;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Helper functions (unchanged)
def get_mapping_columns(i):
    suffix = "" if i == 1 else f" {i}"
    return {
        "mapping":       f"NIST mapping{suffix}",
        "text":          f"Text{suffix}",
        "final":         f"Final Score{suffix}",
        "embedding":     f"Dense{suffix}",
        "ontology":      f"Ontology Score{suffix}",
        "commonality":   f"Commonality{suffix}",
        "justification": f"Justification{suffix}",
        "differences":   f"Differences{suffix}",
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
        code, name  = short_mapping_label(raw_mapping)

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
            ),
        })

    results = sorted(results, key=lambda x: x["final"], reverse=True)
    return results[:top_k]

def score_to_node_colors(score):
    if score >= 0.85:
        return "#059669", "rgba(5,150,105,0.45)",  "white", "#34d399"
    elif score >= 0.70:
        return "#d97706", "rgba(217,119,6,0.45)",  "white", "#fcd34d"
    else:
        return "#dc2626", "rgba(220,38,38,0.45)",  "white", "#fca5a5"

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
        name   = parts[-1]
        if len(name) > 12:
            name = name[:11] + "…"
        return number, name
    if len(mapping) > 9:
        return mapping[:9], mapping[9:]
    return mapping, ""

# PDF and SVG functions omitted for brevity (use previous code or your implementation)

# Main app
DATA_FILE = "final_with_explanations_COMPLETE.csv"

if os.path.exists(DATA_FILE):

    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    if "ECC id control" not in df.columns:
        st.error("Column 'ECC id control' was not found in the CSV file.")
        st.stop()

    st.sidebar.title("🔒 ECC Controls")
    search_term = st.sidebar.text_input(
        "Search ECC Control",
        placeholder="e.g. 1-1 or PR.AA",
        key="search_term",
    )

    all_control_ids = sorted(
        df["ECC id control"].astype(str).unique(),
        key=natural_control_sort,
    )

    if search_term.strip():
        filtered_ids = [
            cid for cid in all_control_ids
            if search_term.strip().lower() in cid.lower()
        ]
    else:
        filtered_ids = all_control_ids

    if not filtered_ids:
        st.sidebar.warning("No controls match your search.")
        filtered_ids = all_control_ids

    if "selected_id" not in st.session_state:
        st.session_state.selected_id = all_control_ids[0]

    exact_match = next(
        (cid for cid in all_control_ids
         if cid.lower() == search_term.strip().lower()),
        None,
    )
    if exact_match and exact_match != st.session_state.selected_id:
        st.session_state.selected_id = exact_match

    radio_default_idx = (
        filtered_ids.index(st.session_state.selected_id)
        if st.session_state.selected_id in filtered_ids
        else 0
    )

    selected_id = st.sidebar.radio(
        "Select Control ID",
        filtered_ids,
        index=radio_default_idx,
        format_func=lambda x: x,
    )
    st.session_state.selected_id = selected_id

    # Load row
    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    source_text_col = find_col(list(df.columns), "Source Text")
    source_text = safe_value(row.get(source_text_col, "") if source_text_col else "")

    # Header sections
    header_col1, header_col2 = st.columns([4, 1.4])

    with header_col1:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg,#0f172a 0%,#312e81 60%,#4c1d95 100%);
                border-radius: 12px 0 0 12px;
                padding: 20px 28px; margin-bottom: 10px;
                min-height: 110px;
                display: flex; flex-direction: column; justify-content: center;
            ">
                <div style="font-size:11px;font-weight:600;color:#a5b4fc; text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">
                    ECC–NIST Framework
                </div>
                <h1 style="margin:0;font-size:26px;color:#f8fafc; font-family:'Inter',Arial,sans-serif; font-weight:800;line-height:1.2;">
                    Control Mapping Viewer
                </h1>
                <p style="margin-top:8px;color:#94a3b8;font-size:13px; font-family:'Inter',Arial,sans-serif;">
                    Active control:
                    <span style="color:#a5b4fc;font-weight:700;">{selected_id}</span>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with header_col2:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg,#f5f7ff 0%,#eef2ff 100%);
                border: 1px solid #c7d2fe;
                border-radius: 0 12px 12px 0;
                padding: 16px 18px; margin-bottom: 10px;
                min-height: 110px;
                display: flex; flex-direction: column; justify-content: center;
            ">
                <p style="margin:0 0 10px 0;font-weight:700;color:#4f46e5; font-size:12px;text-transform:uppercase;letter-spacing:0.5px;">
                    <details style="margin:0; padding:0;">
                      <summary style="cursor:pointer;">🔽 Top-K Mappings</summary>
                      <div style="padding:8px 0;">
                        Select number of top mappings.
                      </div>
                    </details>
                </p>
                """,
            unsafe_allow_html=True,
        )
        top_k = st.select_slider(
            "Top-K Recommendations",
            options=list(range(1, 6)),
            value=5,
            label_visibility="collapsed",
        )

    mappings = extract_mappings(row, df, top_k=top_k)

    st.markdown(
        f"""
        <div style="margin-top:-8px;margin-bottom:8px;color:#64748b;font-size:13px;">
            Showing <b style="color:#6366f1;">{len(mappings)}</b> recommended mapping(s) for
            <b style="color:#4f46e5;">{selected_id}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Create a container with scroll
    viewer_container = st.container()
    with viewer_container:
        # Add toggle button for circles
        if "circles_hidden" not in st.session_state:
            st.session_state.circles_hidden = False

        def toggle_circles():
            st.session_state.circles_hidden = not st.session_state.circles_hidden

        st.markdown(
            f'<button onclick="toggleCircles()" style="margin:8px; padding:6px 12px; background:#6366f1; color:#fff; border:none; border-radius:6px; cursor:pointer;">{"Show Circles" if st.session_state.circles_hidden else "Hide Circles"}</button>',
            unsafe_allow_html=True
        )

        # Generate viewer html
        viewer_html = create_svg_viewer(
            selected_id=str(selected_id),
            source_text=source_text,
            mappings=mappings,
            hide_circles=st.session_state.circles_hidden
        )

        # Fix height and enable scrolling
        height_px = 600  # or calculate based on content
        components.html(viewer_html, height=height_px, scrolling=True)

    # Export PDF section (unchanged)
    st.markdown(
        """
        <div style="height:1px; background:linear-gradient(90deg,#e8edff,#c7d2fe,#e8edff); margin:16px 0 14px 0;"></div>
        <div style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:10px;">
            Export Mapping Report
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Generate PDF (assuming generate_pdf is defined)
    # pdf_bytes = generate_pdf(selected_id, source_text, mappings)
    # if pdf_bytes:
    #     st.download_button("⬇ Export PDF Report", pdf_bytes, f"{selected_id}_mapping_report.pdf", "application/pdf")
    # else:
    #     st.warning("PDF export requires the `fpdf2` library.")

else:
    st.markdown(
        f"""
        <div style="background:#fef2f2; border:1px solid #fecaca; border-radius:10px; padding:24px; margin-top:30px;">
            <div style="font-size:16px;font-weight:700;color:#991b1b;margin-bottom:8px;">
                ⚠️ Data file not found
            </div>
            <div style="color:#7f1d1d;font-size:14px;">
                Make sure <code>{DATA_FILE}</code> is in the same folder as <code>mapviewer.py</code>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------- SVG Viewer with fixes ---------
import html

def create_svg_viewer(selected_id, source_text, mappings, hide_circles=False):
    width = 620
    height = 600  # increased for scroll fix
    center_x = 310
    center_y = 220
    blue_radius = 48
    green_radius = 42
    graph_radius = 158

    mapping_data = {}
    svg_lines = ""
    svg_nodes = ""
    svg_numbers = ""

    n = len(mappings)

    source_short = source_text if len(source_text) <= 160 else source_text[:157] + "…"

    for idx, item in enumerate(mappings):
        angle = (2 * math.pi / n) * idx - (math.pi / 2)
        x = center_x + graph_radius * math.cos(angle)
        y = center_y + graph_radius * math.sin(angle)
        rank = idx + 1
        node_id = f"node_{rank}"

        fill_color, glow_color, text_color, badge_color = score_to_node_colors(item["final"])
        score_pct = format_percent(item["final"])
        code_escaped = html.escape(item["short_code"])

        # Save data for interaction
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
            "ontology": format_decimal(item["ontology"]),
            "ontology_percent": format_percent(item["ontology"]),
            "commonality": item["commonality"],
            "justification": item["justification"],
            "differences": item["differences"],
            "fill_color": fill_color,
            "badge_color": badge_color,
        }

        dx = x - center_x
        dy = y - center_y
        distance = math.sqrt(dx * dx + dy * dy)

        start_x = center_x + (blue_radius / distance) * dx
        start_y = center_y + (blue_radius / distance) * dy
        end_x = x - (green_radius / distance) * dx
        end_y = y - (green_radius / distance) * dy

        # Draw lines
        svg_lines += f"""
            <line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}"
                  stroke="{fill_color}" stroke-width="1.8"
                  stroke-dasharray="5,3" opacity="0.6"/>
        """

        # Number label with data attribute for color update
        svg_numbers += f"""
            <text x="{x}" y="{y - green_radius - 9}"
                  data-node-id="{node_id}"
                  class="number-label" fill="{fill_color}">{rank}</text>
        """

        # Circles and text for node
        if not hide_circles:
            svg_nodes += f"""
                <g class="mapping-node" onclick="updatePanel('{node_id}')" data-fill="{fill_color}" data-glow="{glow_color}">
                    <circle cx="{x}" cy="{y}" r="{green_radius + 5}" fill="{fill_color}" opacity="0.18" class="glow-ring"/>
                    <circle cx="{x}" cy="{y}" r="{green_radius}" fill="{fill_color}" filter="drop-shadow(0 3px 8px {glow_color})"/>
                    <text x="{x}" y="{y - 8}" text-anchor="middle" dominant-baseline="middle" class="node-code">{code_escaped}</text>
                    <text x="{x}" y="{y + 10}" text-anchor="middle" dominant-baseline="middle" class="node-score">{html.escape(score_pct)}</text>
                </g>
            """

    mapping_json = json.dumps(mapping_data)
    source_json = json.dumps(source_text)
    selected_id_json = json.dumps(str(selected_id))

    # Generate HTML
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: 'Inter', Arial, sans-serif;
                background: #f8faff;
                color: #1e293b;
            }}
            .main-card {{
                width: 100%;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                overflow: hidden;
                background: white;
                display: flex;
                flex-direction: column;
                box-shadow: 0 2px 4px rgba(99,102,241,0.05),
                            0 8px 24px rgba(99,102,241,0.08);
            }}
            /* Top row */
            .top-row {{
                display: flex;
                flex-direction: column;
                height: 100%;
            }}
            /* Graph section with fixed height and scroll */
            .graph-section {{
                height: 600px;
                overflow-y: auto;
                position: relative;
                background: linear-gradient(145deg, #f5f7ff 0%, #eef2ff 100%);
                width: 100%;
            }}
            /* Button style for toggle circles */
            button {{
                margin: 8px;
                padding: 6px 12px;
                background:#6366f1;
                color:#fff;
                border:none;
                border-radius:6px;
                cursor:pointer;
                font-size: 13px;
                font-weight: 600;
            }}
            /* SVG styles */
            svg {{
                width: 100%;
                height: 100%;
            }}
            /* Node hover effect */
            .mapping-node:hover .glow-ring {{
                opacity: 0.38 !important;
            }}
            /* Number label style */
            .number-label {{
                font-size: 10px;
                font-weight: 700;
                font-family: 'Inter', Arial, sans-serif;
            }}
        </style>
    </head>
    <body>
        <div class="main-card">
            <!-- Top row with toggle button -->
            <div class="top-row">
                <button id="toggleCircles" onclick="toggleCircles()">Hide Circles</button>
                <!-- SVG container -->
                <div class="graph-section" id="svg-container">
                    <svg viewBox="0 0 {width} {height}">
                        <circle cx="{center_x}" cy="{center_y}" r="{graph_radius}" fill="none" stroke="#c7d2fe" stroke-dasharray="3,6" opacity="0.5"/>
                        {svg_lines}
                        {svg_nodes}
                        {svg_numbers}
                        <defs>
                            <linearGradient id="centerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" style="stop-color:#818cf8"/>
                                <stop offset="100%" style="stop-color:#4f46e5"/>
                            </linearGradient>
                            <radialGradient id="centerGlow">
                                <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1"/>
                                <stop offset="100%" style="stop-color:#6366f1;stop-opacity:0"/>
                            </radialGradient>
                        </defs>
                        <!-- ECC center node -->
                        <g class="center-node" onclick="showEccPanel()">
                            <circle cx="{center_x}" cy="{center_y}" r="{blue_radius + 10}" fill="url(#centerGlow)" opacity="0.22"/>
                            <circle cx="{center_x}" cy="{center_y}" r="{blue_radius}" fill="url(#centerGrad)" filter="drop-shadow(0 4px 14px rgba(99,102,241,0.55))"/>
                            <text x="{center_x}" y="{center_y - 8}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="13" font-weight="800" font-family="Inter, Arial, sans-serif">ECC</text>
                            <text x="{center_x}" y="{center_y + 8}" text-anchor="middle" dominant-baseline="middle" fill="rgba(255,255,255,0.85)" font-size="10" font-weight="700" font-family="Inter, Arial, sans-serif">{html.escape(str(selected_id))}</text>
                            <text x="{center_x}" y="{center_y + 22}" text-anchor="middle" dominant-baseline="middle" fill="rgba(255,255,255,0.55)" font-size="8" font-weight="500" font-family="Inter, Arial, sans-serif">click</text>
                        </g>
                    </svg>
                </div>
            </div>
            <!-- Bottom section: details and results -->
            <div style="display:flex; flex-direction:column; padding:10px;">
                <!-- Results summary -->
                <div class="results-summary" style="margin-top:10px;">
                    <div class="results-summary-title">
                        📋 Results Summary —
                        <span style="color:#6366f1;">{len(mappings)}</span>
                        &nbsp;for&nbsp;
                        <b style="color:#4f46e5;">{html.escape(str(selected_id))}</b>
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
                <!-- Placeholder / detailed panel -->
                <div id="detailPanel" class="summary-section" style="margin-top:10px;">
                    <div class="placeholder" style="text-align:center; padding:40px;">
                        <div style="font-size:32px; margin-bottom:12px;">🔗</div>
                        <div>Click any node to view<br>detailed mapping info</div>
                        <div style="font-size:11px; color:#a5b4fc; margin-top:6px;">
                            Click the blue ECC node for the control description
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <!-- JS for interactions -->
        <script>
            const mappingData = {mapping_json};
            const summaryRows = {json.dumps([{
                "rank": str(i+1),
                "nist_control": m["mapping"],
                "final_percent": format_percent(m["final"]),
                "final": format_decimal(m["final"]),
                "fill_color": score_to_node_colors(m["final"])[0],
                "badge_color": score_to_node_colors(m["final"])[3],
            } for i, m in enumerate(mappings)])};
            let circlesHidden = false;

            function showEccPanel() {{
                const panel = document.getElementById("detailPanel");
                panel.innerHTML = `
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
                        <div style="font-size:24px;">🔵</div>
                        <div>
                            <div style="font-weight:700; font-size:15px;">ECC Control</div>
                            <div style="font-size:11px; color:#94a3b8;">Source control description</div>
                        </div>
                    </div>
                    <div style="font-weight:600; font-size:13px; color:#4f46e5;">Control ID: ${html.escape(selected_id)}</div>
                    <div style="margin-top:8px; line-height:1.5;">${html.escape(source_text)}</div>
                    <div style="margin-top:12px; font-weight:600; font-size:13px; color:#4f46e5;">Click a node for details</div>
                `;
            }}

            function updatePanel(nodeId) {
                const item = mappingData[nodeId];
                if (!item) return;
                const finalVal = parseFloat(item.final);
                const matchIcon = finalVal >= 0.85 ? "🟢" : finalVal >= 0.70 ? "🟡" : "🔴";
                const matchLabel = finalVal >= 0.85 ? "High Match" : finalVal >= 0.70 ? "Medium Match" : "Low Match";
                const domain = item.nist_control.startsWith("GV") ? "Govern" :
                               item.nist_control.startsWith("ID") ? "Identify" :
                               item.nist_control.startsWith("PR") ? "Protect" :
                               item.nist_control.startsWith("DE") ? "Detect" :
                               item.nist_control.startsWith("RS") ? "Respond" :
                               item.nist_control.startsWith("RC") ? "Recover" : "Unknown";

                document.getElementById("detailPanel").innerHTML = \`
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
                        <div style="font-size:24px;">\${matchIcon}</div>
                        <div>
                            <div style="font-weight:700; font-size:15px;">Mapping #\${item.rank} Details</div>
                            <div style="font-size:11px; color:#94a3b8;">\${html.escape(item.nist_control)}</div>
                        </div>
                    </div>
                    <div style="margin-top:8px; font-weight:600;">Scores & Analysis</div>
                    <div style="display:flex; gap:10px; margin-top:4px;">
                        <div style="background:#6366f1; color:#fff; padding:8px; border-radius:8px; flex:1;">
                            <div style="font-size:11px;">Final Score</div>
                            <div style="font-weight:700; font-size:14px;">\${html.escape(item.final_percent)}</div>
                        </div>
                        <div style="background:#0891b2; color:#fff; padding:8px; border-radius:8px; flex:1;">
                            <div style="font-size:11px;">Embedding</div>
                            <div style="font-weight:700; font-size:14px;">\${html.escape(item.embedding)}</div>
                        </div>
                        <div style="background:#059669; color:#fff; padding:8px; border-radius:8px; flex:1;">
                            <div style="font-size:11px;">Ontology</div>
                            <div style="font-weight:700; font-size:14px;">\${html.escape(item.ontology)}</div>
                        </div>
                    </div>
                    <div style="margin-top:8px; font-size:12px;">Confidence: <b>\${matchLabel}</b></div>
                    <div style="margin-top:8px; font-weight:600;">NIST Control</div>
                    <div style="margin-bottom:8px;">\${html.escape(item.nist_control)}</div>
                    <div style="margin-top:8px; font-weight:600;">Commonality</div>
                    <div>\${html.escape(item.commonality)}</div>
                    <div style="margin-top:8px; font-weight:600;">Justification</div>
                    <div>\${html.escape(item.justification)}</div>
                    <div style="margin-top:8px; font-weight:600;">Differences</div>
                    <div>\${html.escape(item.differences)}</div>
                \`;
            }}

            function toggleCircles() {
                const nodes = document.querySelectorAll('.mapping-node');
                for (const node of nodes) {
                    node.style.display = (node.style.display === 'none') ? 'block' : 'none';
                }
                document.getElementById('toggleCircles').innerText = (
                    document.getElementById('toggleCircles').innerText === 'Hide Circles' ? 'Show Circles' : 'Hide Circles'
                );
            }

            // After DOM loads, assign initial number colors
            document.addEventListener("DOMContentLoaded", () => {
                updateNumberColors({json.dumps(str(selected_id))});
            });

            function updateNumberColors(selectedNodeId) {
                document.querySelectorAll('.number-label').forEach(lbl => {
                    const nodeId = lbl.getAttribute('data-node-id');
                    lbl.setAttribute('fill', nodeId === selectedNodeId ? 'white' : '#6366f1');
                });
            }
        </script>
    </body>
    </html>
    """
    return html_code
