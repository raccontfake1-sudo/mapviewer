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
            font-family: 'Inter', sans-serif !important;
        }

        .main .block-container {
            padding-top: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100%;
        }

        /* General Page Background */
        body {
            background-color: #f8fafc;
            color: #1e293b;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
            border-right: 1px solid #e2e8f0;
        }

        /* BaseWeb Slider Styling — White Labels for 1 and 5 */
        .stSlider [data-baseweb="slider"] [data-testid="stTickBar"] span,
        .stSlider [data-baseweb="slider"] [role="slider"] + div span,
        .stSlider [data-baseweb="slider"] [class*="Tick"],
        .stSlider [data-baseweb="slider"] [class*="InnerThumb"] + div,
        .stSlider [data-baseweb="slider"] div[role="slider"] ~ div,
        .stSlider [data-baseweb="slider"] [data-testid="stSliderTickBar"] div,
        [data-testid="stBaseButton-secondary"] {
            color: #ffffff !important;
        }

        .stSlider label, .stSlider p {
            color: #ffffff !important;
        }

        /* Metric Cards */
        div[data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        div[data-testid="metric-container"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.08);
        }
        div[data-testid="metric-container"] > div {
            justify-content: center;
        }
        div[data-testid="metric-container"] label p {
            font-weight: 600 !important;
            font-size: 1.05rem;
            color: #475569;
        }

        /* Dataframes / Tables */
        .stDataFrame {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .stDataFrame td, .stDataFrame th {
            padding: 12px 16px !important;
        }
        .stDataFrame th {
            background-color: #f1f5f9 !important;
            color: #334155 !important;
            font-weight: 600 !important;
        }
        .stDataFrame tbody tr:nth-child(even) {
            background-color: #f8fafc;
        }
        .stDataFrame tbody tr:hover {
            background-color: #e2e8f0;
            cursor: default;
        }

        /* Radio Buttons in Sidebar */
        div[data-testid="stRadio"] label {
            font-weight: 500 !important;
            color: #334155;
        }
        div[data-testid="stRadio"] > div {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px;
        }

        /* Headings */
        h1 { color: #0f172a; font-weight: 700 !important; }
        h2 { color: #1e293b; font-weight: 600 !important; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 1.5rem !important; }
        h3 { color: #334155; font-weight: 600 !important; margin-top: 1rem !important; }

        /* Expanders */
        .streamlit-expanderHeader {
            font-weight: 600 !important;
            color: #334155 !important;
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
        }
        .streamlit-expanderContent {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-top: none;
            border-radius: 0 0 8px 8px;
            padding: 1.5rem;
        }

        /* Buttons */
        div[data-testid="stButton"] button {
            background-color: #2563eb;
            color: #ffffff;
            border-radius: 6px;
            padding: 0.5rem 1.2rem;
            font-weight: 500;
            transition: all 0.2s;
        }
        div[data-testid="stButton"] button:hover {
            background-color: #1d4ed8;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
            transform: translateY(-1px);
        }
        div[data-testid="stDownloadButton"] button {
            background-color: #10b981 !important;
            color: #ffffff !important;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s;
        }
        div[data-testid="stDownloadButton"] button:hover {
            background-color: #059669 !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
            transform: translateY(-1px);
        }

        /* Tooltips */
        .stTooltipIcon {
            color: #94a3b8;
        }
        .stTooltipContent {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
            border-radius: 8px !important;
        }

        /* Spinner & Toast */
        .stSpinner > div {
            border-top-color: #2563eb !important;
        }
        .stToast {
            border: 1px solid #e2e8f0;
            background-color: #ffffff;
            color: #1e293b;
        }

        /* Custom Pill */
        .pill {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            color: #ffffff;
            background-color: #3b82f6;
            margin-right: 8px;
        }

        /* ECC compact header */
        .ecc-header {
            background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 20px;
            color: #ffffff;
            box-shadow: 0 4px 20px rgba(30, 58, 138, 0.25);
        }
        .ecc-header h2 { color: #ffffff !important; border-bottom: none; margin: 0; padding: 0; }
        .ecc-header p { margin: 4px 0 0 0; opacity: 0.9; font-size: 0.95rem; }
        .ecc-header .pill { background: rgba(255,255,255,0.2); color: #ffffff; }

        /* Detail panel card */
        .detail-card {
            background: #ffffff;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            padding: 20px;
            margin-top: 12px;
            max-height: 400px;
            overflow-y: auto;
        }

        /* Top bar area background for slider label contrast */
        .top-bar-bg {
            background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            color: #ffffff;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    return df

uploaded_file = st.sidebar.file_uploader("Upload your mapped CSV", type=["csv"])

if uploaded_file is None:
    st.info("Please upload your `final_with_explanations_COMPLETE.csv` file via the sidebar to begin.")
    st.stop()

df = load_data(uploaded_file)

if "ECC Control" not in df.columns or "NIST Control" not in df.columns:
    st.error("CSV must contain 'ECC Control' and 'NIST Control' columns.")
    st.stop()

ecc_list = sorted(df["ECC Control"].dropna().unique())
nist_list = sorted(df["NIST Control"].dropna().unique())

ecc_lookup = {row["ECC Control"]: row for _, row in df.iterrows()}
nist_lookup = {row["NIST Control"]: row for _, row in df.iterrows()}

# Sidebar search and navigation
st.sidebar.title("Navigation")
search_query = st.sidebar.text_input("Search Control", placeholder="e.g., AC-2 or ECC-1.1")
controls_to_show = ecc_list
if search_query:
    q = search_query.lower().strip()
    controls_to_show = [c for c in ecc_list if q in str(c).lower()]
    if not controls_to_show:
        st.sidebar.warning("No ECC controls found.")
        controls_to_show = ecc_list

control_mode = st.sidebar.radio("View Mode", ["List All ECC Controls", "Top-K Mapping"])

if control_mode == "Top-K Mapping":
    st.markdown('<div class="top-bar-bg">', unsafe_allow_html=True)
    top_k = st.slider("Top-K Mapping", min_value=1, max_value=5, value=3, help="Select how many NIST controls to display.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    top_k = None

# Select control
selected_control = st.sidebar.selectbox("Select ECC Control", controls_to_show)

# PDF Export helper
def create_pdf(title, content_html):
    try:
        from fpdf import FPDF
    except ImportError:
        st.error("`fpdf2` is required for PDF export. Install with: `pip install fpdf2`")
        return None

    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 14)
            self.set_text_color(30, 58, 138)
            self.cell(0, 10, title, ln=True, align="C")
            self.ln(4)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(30, 41, 59)

    # Simple HTML strip for PDF
    clean = re.sub(r"<[^>]+>", "", content_html)
    clean = html.unescape(clean)
    for line in clean.split("\n"):
        pdf.multi_cell(0, 6, line)

    return pdf.output(dest="S").encode("latin-1")

# Layout: Graph and side panel
col_graph, col_side = st.columns([4, 1])

# Build graph data
selected_row = ecc_lookup.get(selected_control, {})
target_nodes = []
edges = []

if control_mode == "Top-K Mapping":
    for i in range(1, 6):
        nist_col = f"NIST Control {i}"
        conf_col = f"Confidence Score {i}"
        expl_col = f"Explanation {i}"
        if nist_col in selected_row and pd.notna(selected_row.get(nist_col)):
            nist_id = str(selected_row[nist_col]).strip()
            if nist_id:
                conf = selected_row.get(conf_col, "N/A")
                expl = selected_row.get(expl_col, "")
                target_nodes.append({
                    "id": nist_id,
                    "confidence": conf,
                    "explanation": expl,
                    "index": i,
                })
    target_nodes = target_nodes[:top_k]
    edges = [{"source": selected_control, "target": n["id"], "confidence": n["confidence"]} for n in target_nodes]
else:
    # List all: find all rows for this ECC control
    ecc_rows = df[df["ECC Control"] == selected_control]
    seen = set()
    for _, row in ecc_rows.iterrows():
        for i in range(1, 6):
            nist_col = f"NIST Control {i}"
            if nist_col in row and pd.notna(row.get(nist_col)):
                nist_id = str(row[nist_col]).strip()
                if nist_id and nist_id not in seen:
                    seen.add(nist_id)
                    target_nodes.append({
                        "id": nist_id,
                        "confidence": row.get(f"Confidence Score {i}", "N/A"),
                        "explanation": row.get(f"Explanation {i}", ""),
                        "index": i,
                    })
    edges = [{"source": selected_control, "target": n["id"], "confidence": n["confidence"]} for n in target_nodes]

# Create interactive SVG viewer
def create_svg_viewer(source_id, nodes, edges_data):
    width = 700
    height = max(500, 120 + len(nodes) * 90)
    node_positions = {}

    # Layout source at left center, targets stacked on right
    source_x = 140
    source_y = height // 2
    node_positions[source_id] = (source_x, source_y)

    start_y = 80
    gap = (height - 160) // max(len(nodes), 1)
    for idx, node in enumerate(nodes):
        nx = width - 140
        ny = start_y + idx * gap
        node_positions[node["id"]] = (nx, ny)

    def make_node_circle(nid, x, y, r, fill, label, is_source=False):
        cls = "node-source" if is_source else "node-target"
        title = html.escape(label)
        return f"""
        <g class="node-group" data-id="{html.escape(str(nid))}" onclick="showDetail(event, '{html.escape(str(nid))}')">
            <circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="#ffffff" stroke-width="3" class="{cls}" style="cursor:pointer; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.2));" />
            <text x="{x}" y="{y+5}" text-anchor="middle" fill="#ffffff" font-size="13" font-weight="700" style="pointer-events:none;">{title[:16]}</text>
            <title>{html.escape(str(nid))}</title>
        </g>
        """

    def make_edge(x1, y1, x2, y2, confidence):
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        conf_text = str(confidence) if confidence not in (None, "", "N/A") else ""
        edge_html = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrowhead)" />'
        if conf_text:
            badge = f"""
            <rect x="{mid_x-20}" y="{mid_y-12}" width="40" height="24" rx="12" fill="#2563eb" opacity="0.95" />
            <text x="{mid_x}" y="{mid_y+4}" text-anchor="middle" fill="#ffffff" font-size="11" font-weight="600">{conf_text}</text>
            """
            edge_html += badge
        return edge_html

    svg_nodes = []
    svg_edges = []

    for nid, (x, y) in node_positions.items():
        is_src = nid == source_id
        fill = "#1d4ed8" if is_src else "#10b981"
        r = 45 if is_src else 38
        svg_nodes.append(make_node_circle(nid, x, y, r, fill, nid, is_src))

    for e in edges_data:
        sx, sy = node_positions.get(e["source"], (0, 0))
        tx, ty = node_positions.get(e["target"], (0, 0))
        svg_edges.append(make_edge(sx, sy, tx, ty, e.get("confidence")))

    # Prepare detail content mapping
    detail_map = {}
    for n in nodes:
        detail_map[n["id"]] = {
            "id": n["id"],
            "confidence": n.get("confidence", "N/A"),
            "explanation": n.get("explanation", "")
        }
    # Source detail
    detail_map[source_id] = {
        "id": source_id,
        "confidence": "-",
        "explanation": selected_row.get("Source Description", "No description available.")
    }

    detail_json = html.escape(json.dumps(detail_map))

    svg_content = f"""
    <svg width="100%" height="100%" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="background: #f8fafc; border-radius: 12px;">
        <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
            </marker>
        </defs>
        {''.join(svg_edges)}
        {''.join(svg_nodes)}
    </svg>
    """

    html_code = f"""
    <div id="graph-wrapper" style="width:100%; height:{height}px; border-radius:12px; overflow:hidden; position:relative;">
        {svg_content}
    </div>
    <script>
        var detailData = JSON.parse("{detail_json}");
        var originalSvg = document.getElementById("graph-wrapper").innerHTML;

        function showDetail(evt, nodeId) {{
            evt.stopPropagation();
            var panel = document.getElementById("detail-panel");
            if (!panel) return;
            var data = detailData[nodeId];
            if (!data) return;
            var html = '<div style=\"margin-bottom:12px;\"><span class=\"pill\">' + escapeHtml(data.id) + '</span></div>';
            html += '<p style=\"color:#475569; margin-bottom:8px;\"><strong>Confidence:</strong> ' + escapeHtml(String(data.confidence)) + '</p>';
            html += '<div style=\"color:#334155; line-height:1.6;\">' + escapeHtml(data.explanation) + '</div>';
            panel.innerHTML = html;
            panel.style.display = "block";
        }}

        function escapeHtml(text) {{
            if (!text) return "";
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }}

        function showSourceDetail() {{
            showDetail({{stopPropagation: function(){{}}}}, "{html.escape(str(source_id))}");
        }}
    </script>
    """
    return html_code

with col_graph:
    st.subheader("Mapping Graph")
    if not target_nodes:
        st.info("No mapped NIST controls found for this ECC control.")
    else:
        components.html(
            create_svg_viewer(selected_control, target_nodes, edges),
            height=max(500, 120 + len(target_nodes) * 90),
            scrolling=True,
        )

# ECC compact header in main panel
ecc_name = selected_control
ecc_title = str(selected_row.get("ECC Title", "")) if "ECC Title" in selected_row else ""
ecc_desc = str(selected_row.get("Source Description", "No description available."))

st.markdown(f"""
<div class="ecc-header" onclick="if(window.showSourceDetail)window.showSourceDetail()">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="font-size:0.8rem; text-transform:uppercase; letter-spacing:1px; opacity:0.8; margin-bottom:4px;">ECC Control</div>
            <h2 style="margin:0; padding:0;">{html.escape(ecc_name)}</h2>
            <p style="margin-top:6px;">{html.escape(ecc_title)}</p>
        </div>
        <div style="text-align:right;">
            <span class="pill">Mapped to {len(target_nodes)} NIST</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Detail panel placed right after header so it scrolls naturally with the page
st.markdown('<div id="detail-panel" class="detail-card" style="display:none;"></div>', unsafe_allow_html=True)

# Results table
st.subheader("Mapped NIST Controls")

if not target_nodes:
    st.warning("No mapped NIST controls to display.")
else:
    table_data = []
    for n in target_nodes:
        table_data.append({
            "NIST Control": n["id"],
            "Confidence": n["confidence"],
            "Explanation": n["explanation"],
        })

    df_table = pd.DataFrame(table_data)

    # Custom bar chart for confidence scores
    def confidence_bar(val):
        try:
            v = float(val)
            pct = max(0, min(100, v * 100))
            color = "#10b981" if pct >= 80 else "#f59e0b" if pct >= 50 else "#ef4444"
            return f"""
            <div style="width:100%; background:#f1f5f9; border-radius:6px; overflow:hidden;">
                <div style="width:{pct:.0f}%; background:{color}; height:18px; border-radius:6px;"></div>
            </div>
            <div style="text-align:center; font-size:0.8rem; color:#475569; margin-top:2px;">{v:.2f}</div>
            """
        except:
            return f'<span style="color:#94a3b8;">{val}</span>'

    st.dataframe(
        df_table,
        use_container_width=True,
        column_config={
            "NIST Control": st.column_config.TextColumn("NIST Control", width="medium"),
            "Confidence": st.column_config.Column("Confidence", width="small", help="Higher is better"),
            "Explanation": st.column_config.TextColumn("Explanation", width="large"),
        },
        hide_index=True,
    )

    with st.expander("View Confidence Score Breakdown"):
        for _, row in df_table.iterrows():
            st.markdown(f"**{row['NIST Control']}**", unsafe_allow_html=True)
            st.markdown(confidence_bar(row["Confidence"]), unsafe_allow_html=True)

    # PDF Export
    export_html = f"<h1>ECC-NIST Mapping Report</h1><h2>{html.escape(ecc_name)}</h2><p>{html.escape(ecc_desc)}</p><hr/>"
    for n in target_nodes:
        export_html += f"<h3>{html.escape(n['id'])}</h3><p><strong>Confidence:</strong> {html.escape(str(n['confidence']))}</p><p>{html.escape(str(n['explanation']))}</p>"

    pdf_bytes = create_pdf(f"Mapping Report: {selected_control}", export_html)
    if pdf_bytes:
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=f"mapping_report_{selected_control.replace(' ', '_')}.pdf",
            mime="application/pdf",
        )

# Right side panel metrics
with col_side:
    st.metric("ECC Controls", len(ecc_list))
    st.metric("NIST Controls", len(nist_list))
    st.metric("Mappings", len(df))

    st.markdown("---")
    st.markdown("### Selected")
    st.markdown(f"**ECC:** `{selected_control}`")
    st.markdown(f"**Mappings:** `{len(target_nodes)}`")

    if st.button("Reset Zoom"):
        st.toast("Zoom reset (graph auto-fits on refresh)", icon="🔄")

st.markdown("---")
st.caption("Built with Streamlit · ECC-NIST Control Mapping Viewer")
