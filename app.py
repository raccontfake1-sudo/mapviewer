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

        section[data-testid="stSidebar"] input[type="text"] {
            background: #273549 !important;
            border: 1px solid #475569 !important;
            border-radius: 8px !important;
            color: #f1f5f9 !important;
            font-size: 13px !important;
            padding: 8px 12px !important;
        }

        section[data-testid="stSidebar"] input[type="text"]::placeholder {
            color: #64748b !important;
        }

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
            background: #334155 !important;
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

        /* FIX 1: Remove all top space */
        .main .block-container {
            padding-top: 0px !important;
            margin-top: 0px !important;
            padding-bottom: 24px !important;
        }

        /* Also target the appview block */
        .block-container {
            padding-top: 0px !important;
            margin-top: 0px !important;
        }

        /* Remove Streamlit default top padding */
        div[data-testid="stAppViewBlockContainer"] {
            padding-top: 0px !important;
        }

        /* Remove the empty element gaps above header columns */
        div[data-testid="column"] > div:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

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

        #MainMenu { visibility: hidden; }
        footer    { visibility: hidden; }
        header    { visibility: hidden; }

        .stSlider > div > div > div {
            background: #6366f1 !important;
        }

        /* FIX 2: Top-K slider numbers (1 and 5) in white */
        div[data-testid="stSelectSlider"] label,
        div[data-testid="stSelectSlider"] label p,
        div[data-testid="stSelectSlider"] p,
        div[data-testid="stSelectSlider"] span,
        div[data-testid="stSelectSlider"] div {
            color: white !important;
        }

        /* FIX 3: shift ECC header block left */
        div[data-testid="column"]:first-child {
            padding-right: 0px !important;
        }

        div[data-testid="column"]:first-child > div {
            margin-right: 8px !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
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
        name   = parts[-1]
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
        cols               = get_mapping_columns(i)
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


# ─────────────────────────────────────────
# PDF Export
# ─────────────────────────────────────────
def generate_pdf(selected_id, source_text, mappings):
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 12, "ECC-NIST Control Mapping Report", ln=True, align="C")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 7, f"ECC Control: {selected_id}", ln=True, align="C")
    pdf.ln(4)

    pdf.set_draw_color(199, 210, 254)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    if source_text and source_text != "N/A":
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(79, 70, 229)
        pdf.cell(0, 7, "ECC Control Description", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(55, 65, 81)
        clean_src = str(source_text).encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 6, clean_src)
        pdf.ln(4)
        pdf.set_draw_color(199, 210, 254)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    for idx, m in enumerate(mappings):
        final_val = float(m["final"])
        if final_val >= 0.85:
            confidence = "High Match"
            r, g, b    = 5, 150, 105
        elif final_val >= 0.70:
            confidence = "Medium Match"
            r, g, b    = 217, 119, 6
        else:
            confidence = "Low Match"
            r, g, b    = 220, 38, 38

        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        header_text = (
            f"  #{idx + 1}  {m['mapping']}"
            f"  -  {format_percent(m['final'])}  ({confidence})"
        )
        pdf.cell(0, 10, header_text, ln=True, fill=True)
        pdf.ln(2)

        def field(label, value):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(79, 70, 229)
            pdf.cell(0, 6, label, ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(55, 65, 81)
            clean = str(value).encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(0, 5.5, clean)
            pdf.ln(2)

        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(79, 70, 229)
        pdf.cell(0, 6, "Scores & Analysis", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(55, 65, 81)
        pdf.cell(
            0, 5.5,
            f"  Final: {format_percent(m['final'])} ({format_decimal(m['final'])})   "
            f"Embedding: {format_percent(m['embedding'])} ({format_decimal(m['embedding'])})   "
            f"Ontology: {format_percent(m['ontology'])} ({format_decimal(m['ontology'])})",
            ln=True,
        )
        pdf.ln(2)

        field("NIST Control Text",  m["text"])
        field("Commonality",        m["commonality"])
        field("Justification",      m["justification"])
        field("Differences",        m["differences"])

        pdf.set_draw_color(199, 210, 254)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    return bytes(pdf.output())


# ─────────────────────────────────────────
# SVG Viewer  — FIX 4: detail panel is INSIDE the right summary column
# ─────────────────────────────────────────
def create_svg_viewer(selected_id, source_text, mappings):
    width  = 620
    height = 440

    center_x     = 310
    center_y     = 220
    blue_radius  = 40
    green_radius = 34
    graph_radius = 150

    mapping_data = {}
    svg_lines    = ""
    svg_nodes    = ""
    svg_numbers  = ""

    n = len(mappings)

    for idx, item in enumerate(mappings):
        angle = (2 * math.pi / n) * idx - (math.pi / 2)
        x = center_x + graph_radius * math.cos(angle)
        y = center_y + graph_radius * math.sin(angle)

        rank    = idx + 1
        node_id = f"node_{rank}"

        fill_color, glow_color, text_color, badge_color = score_to_node_colors(item["final"])
        score_pct    = format_percent(item["final"])
        code_escaped = html.escape(item["short_code"])

        mapping_data[node_id] = {
            "rank":              str(rank),
            "ecc_control":       str(selected_id),
            "ecc_text":          source_text,
            "nist_control":      item["mapping"],
            "nist_short_code":   item["short_code"],
            "nist_short_name":   item["short_name"],
            "nist_text":         item["text"],
            "final":             format_decimal(item["final"]),
            "final_percent":     format_percent(item["final"]),
            "embedding":         format_decimal(item["embedding"]),
            "embedding_percent": format_percent(item["embedding"]),
            "ontology":          format_decimal(item["ontology"]),
            "ontology_percent":  format_percent(item["ontology"]),
            "commonality":       item["commonality"],
            "justification":     item["justification"],
            "differences":       item["differences"],
            "fill_color":        fill_color,
            "badge_color":       badge_color,
        }

        dx       = x - center_x
        dy       = y - center_y
        distance = math.sqrt(dx * dx + dy * dy)

        start_x = center_x + (blue_radius  / distance) * dx
        start_y = center_y + (blue_radius  / distance) * dy
        end_x   = x        - (green_radius / distance) * dx
        end_y   = y        - (green_radius / distance) * dy

        svg_lines += f"""
            <line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}"
                  stroke="{fill_color}" stroke-width="1.8"
                  stroke-dasharray="5,3" opacity="0.6"/>
        """

        svg_numbers += f"""
            <text x="{x}" y="{y - green_radius - 9}"
                  text-anchor="middle" dominant-baseline="middle"
                  class="number-label" fill="{fill_color}">#{rank}</text>
        """

        svg_nodes += f"""
            <g class="mapping-node" onclick="updatePanel('{node_id}')"
               data-fill="{fill_color}" data-glow="{glow_color}">
                <circle cx="{x}" cy="{y}" r="{green_radius + 5}"
                        fill="{fill_color}" opacity="0.18" class="glow-ring"/>
                <circle cx="{x}" cy="{y}" r="{green_radius}"
                        fill="{fill_color}"
                        filter="drop-shadow(0 3px 8px {glow_color})"/>
                <text x="{x}" y="{y - 7}"
                      text-anchor="middle" dominant-baseline="middle"
                      class="node-code">{code_escaped}</text>
                <text x="{x}" y="{y + 9}"
                      text-anchor="middle" dominant-baseline="middle"
                      class="node-score">{html.escape(score_pct)}</text>
            </g>
        """

    mapping_json   = json.dumps(mapping_data, ensure_ascii=False)
    source_json    = json.dumps(source_text,  ensure_ascii=False)
    source_id_json = json.dumps(str(selected_id), ensure_ascii=False)

    summary_rows_js = json.dumps([
        {
            "rank":          str(i + 1),
            "nist_control":  m["mapping"],
            "final_percent": format_percent(m["final"]),
            "final":         format_decimal(m["final"]),
            "fill_color":    score_to_node_colors(m["final"])[0],
            "badge_color":   score_to_node_colors(m["final"])[3],
        }
        for i, m in enumerate(mappings)
    ])

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet"
              href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: 'Inter', Arial, sans-serif; background: #f8faff; color: #1e293b; }}

            .main-card {{
                width: 100%;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                overflow: hidden;
                background: white;
                box-shadow: 0 2px 4px rgba(99,102,241,0.05), 0 8px 24px rgba(99,102,241,0.08);
            }}

            /* ── single top row: graph left, right panel right ── */
            .top-row {{
                display: flex;
                min-height: 500px;
            }}

            /* ── Graph (left 58%) ── */
            .graph-section {{
                width: 58%;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(145deg, #f5f7ff 0%, #eef2ff 100%);
                border-right: 1px solid #e2e8f0;
                position: relative;
                flex-shrink: 0;
            }}

            .graph-badge {{
                position: absolute; top: 14px; left: 18px;
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                color: white; font-size: 10px; font-weight: 700;
                letter-spacing: 1px; text-transform: uppercase;
                padding: 4px 10px; border-radius: 20px;
            }}

            .legend {{
                position: absolute; bottom: 14px; left: 18px;
                display: flex; gap: 10px;
            }}
            .legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 10px; font-weight: 600; color: #64748b; }}
            .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}

            /* ── Right panel (42%): table on top, detail below ── */
            .right-panel {{
                width: 42%;
                display: flex;
                flex-direction: column;
                background: #ffffff;
                overflow: hidden;
            }}

            /* Summary table (top half of right panel) */
            .summary-table-section {{
                flex-shrink: 0;
                border-bottom: 1px solid #e8edff;
            }}

            .summary-table-header {{
                padding: 14px 16px 8px;
                background: linear-gradient(135deg, #f8f9ff 0%, #f3f6ff 100%);
                border-bottom: 1px solid #e8edff;
            }}

            .summary-table-title {{
                font-size: 12px; font-weight: 700; color: #374151;
                display: flex; align-items: center; gap: 6px;
            }}

            .summary-table-sub {{
                font-size: 11px; color: #94a3b8; margin-top: 2px;
            }}

            /* FIX 4: Detail section scrolls inside the right panel below the table */
            .detail-section {{
                flex: 1;
                overflow-y: auto;
                padding: 14px 16px;
                background: #ffffff;
            }}

            .detail-section::-webkit-scrollbar {{ width: 4px; }}
            .detail-section::-webkit-scrollbar-track {{ background: #f8faff; }}
            .detail-section::-webkit-scrollbar-thumb {{ background: #c7d2fe; border-radius: 4px; }}

            .results-table {{
                width: 100%; border-collapse: collapse; font-size: 12px;
            }}

            .results-table th {{
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                color: white; padding: 8px 12px; text-align: left;
                font-weight: 600; font-size: 11px;
                text-transform: uppercase; letter-spacing: 0.5px;
                position: sticky; top: 0; z-index: 1;
            }}

            .results-table td {{
                padding: 8px 12px;
                border-bottom: 1px solid #eef2ff;
                color: #374151; vertical-align: middle;
            }}

            .results-table tr:last-child td {{ border-bottom: none; }}
            .results-table tr:hover td {{ background: #eef2ff; cursor: pointer; }}

            .rank-badge {{
                display: inline-flex; align-items: center; justify-content: center;
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                color: white; border-radius: 50%;
                width: 22px; height: 22px; font-weight: 700; font-size: 10px;
            }}

            /* SVG node styles */
            .mapping-node {{ cursor: pointer; }}
            .mapping-node circle {{ transition: all 0.2s ease; }}
            .mapping-node:hover .glow-ring {{ opacity: 0.38 !important; }}
            .node-code {{
                fill: white; font-size: 13px; font-weight: 800;
                pointer-events: none; font-family: 'Inter', Arial, sans-serif;
            }}
            .node-score {{
                fill: rgba(255,255,255,0.92); font-size: 13px; font-weight: 700;
                pointer-events: none; font-family: 'Inter', Arial, sans-serif;
            }}
            .number-label {{ font-size: 10px; font-weight: 700; font-family: 'Inter', Arial, sans-serif; }}
            .center-node {{ cursor: pointer; }}

            /* Detail panel inner elements */
            .panel-header {{
                display: flex; align-items: center; gap: 10px;
                margin-bottom: 12px; padding-bottom: 10px;
                border-bottom: 2px solid #eef2ff;
            }}
            .panel-rank-badge {{
                width: 28px; height: 28px; border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                font-size: 13px; font-weight: 800; color: white; flex-shrink: 0;
            }}
            .panel-title {{ font-size: 14px; font-weight: 700; color: #0f172a; }}

            .sub-title {{
                font-size: 10px; font-weight: 700; color: #6366f1;
                text-transform: uppercase; letter-spacing: 0.8px;
                margin-top: 10px; margin-bottom: 3px;
            }}

            .content-box {{
                border: 1px solid #e8edff; border-radius: 8px;
                padding: 8px 10px; font-size: 11px; line-height: 1.6;
                color: #374151; background: #f8faff; white-space: pre-wrap;
            }}

            .score-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }}
            .score-card {{ border-radius: 8px; padding: 8px 10px; text-align: center; }}
            .score-card-main  {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); grid-column: 1 / -1; }}
            .score-card-embed {{ background: linear-gradient(135deg, #0891b2, #06b6d4); }}
            .score-card-onto  {{ background: linear-gradient(135deg, #059669, #10b981); }}
            .score-card-label {{ font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; opacity: 0.85; color: white; margin-bottom: 2px; }}
            .score-card-value {{ font-size: 18px; font-weight: 800; color: white; line-height: 1; }}
            .score-card-sub   {{ font-size: 9px; color: rgba(255,255,255,0.75); margin-top: 2px; }}

            .confidence-row {{
                display: flex; align-items: center; gap: 6px; margin-top: 6px;
                padding: 6px 10px; border-radius: 8px;
                background: #f8faff; border: 1px solid #e8edff;
                font-size: 11px; color: #374151; font-weight: 500;
            }}

            .placeholder-detail {{
                color: #94a3b8; font-size: 12px; line-height: 1.7; text-align: center;
                padding: 24px 12px; border: 2px dashed #c7d2fe; border-radius: 12px;
                background: #f8faff; margin-top: 4px;
            }}

            .ecc-panel-header {{
                display: flex; align-items: center; gap: 10px;
                margin-bottom: 12px; padding-bottom: 10px;
                border-bottom: 2px solid #eef2ff;
            }}
            .ecc-icon {{
                width: 32px; height: 32px; border-radius: 50%;
                background: linear-gradient(135deg, #6366f1, #4f46e5);
                display: flex; align-items: center; justify-content: center;
                font-size: 14px; flex-shrink: 0;
            }}
        </style>
    </head>
    <body>
        <div class="main-card">
            <div class="top-row">

                <!-- Graph left -->
                <div class="graph-section">
                    <div class="graph-badge">Control Mapping Graph</div>
                    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
                        <circle cx="{center_x}" cy="{center_y}" r="{graph_radius}"
                                fill="none" stroke="#c7d2fe" stroke-width="1"
                                stroke-dasharray="3,6" opacity="0.5"/>
                        {svg_lines}
                        <g class="center-node" onclick="showEccPanel()">
                            <circle cx="{center_x}" cy="{center_y}" r="{blue_radius + 10}"
                                    fill="url(#centerGlow)" opacity="0.22"/>
                            <circle cx="{center_x}" cy="{center_y}" r="{blue_radius}"
                                    fill="url(#centerGrad)"
                                    filter="drop-shadow(0 4px 14px rgba(99,102,241,0.55))"/>
                            <text x="{center_x}" y="{center_y - 9}" text-anchor="middle"
                                  dominant-baseline="middle" fill="white" font-size="14"
                                  font-weight="800" font-family="Inter, Arial, sans-serif">ECC</text>
                            <text x="{center_x}" y="{center_y + 8}" text-anchor="middle"
                                  dominant-baseline="middle" fill="rgba(255,255,255,0.85)"
                                  font-size="11" font-weight="700" font-family="Inter, Arial, sans-serif">
                                {html.escape(str(selected_id))}
                            </text>
                            <text x="{center_x}" y="{center_y + 22}" text-anchor="middle"
                                  dominant-baseline="middle" fill="rgba(255,255,255,0.55)"
                                  font-size="9" font-weight="500" font-family="Inter, Arial, sans-serif">click</text>
                        </g>
                        {svg_nodes}
                        {svg_numbers}
                        <defs>
                            <linearGradient id="centerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%"   style="stop-color:#818cf8"/>
                                <stop offset="100%" style="stop-color:#4f46e5"/>
                            </linearGradient>
                            <radialGradient id="centerGlow">
                                <stop offset="0%"   style="stop-color:#6366f1;stop-opacity:1"/>
                                <stop offset="100%" style="stop-color:#6366f1;stop-opacity:0"/>
                            </radialGradient>
                        </defs>
                    </svg>
                    <div class="legend">
                        <div class="legend-item"><div class="legend-dot" style="background:#059669;"></div>High ≥85%</div>
                        <div class="legend-item"><div class="legend-dot" style="background:#d97706;"></div>Mid ≥70%</div>
                        <div class="legend-item"><div class="legend-dot" style="background:#dc2626;"></div>Low &lt;70%</div>
                    </div>
                </div>

                <!-- Right panel: table + detail -->
                <div class="right-panel">

                    <!-- Summary table (always visible at top of right panel) -->
                    <div class="summary-table-section">
                        <div class="summary-table-header">
                            <div class="summary-table-title">
                                📋 Results —
                                <span style="color:#6366f1;">{len(mappings)} mapping(s)</span>
                                &nbsp;for&nbsp;
                                <b style="color:#4f46e5;">{html.escape(str(selected_id))}</b>
                            </div>
                            <div class="summary-table-sub">Click a row or node to view details</div>
                        </div>
                        <table class="results-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>NIST Control</th>
                                    <th>Score</th>
                                </tr>
                            </thead>
                            <tbody id="summary-tbody"></tbody>
                        </table>
                    </div>

                    <!-- FIX 4: Detail panel scrolls below the table, inside same column -->
                    <div class="detail-section" id="detail-panel">
                        <div class="placeholder-detail">
                            🔗 Click any node or row to view details<br>
                            <span style="color:#a5b4fc;font-size:10px;">
                                Click the blue ECC node for the control description
                            </span>
                        </div>
                    </div>

                </div>
            </div>
        </div>

        <script>
            const mappingData  = {mapping_json};
            const summaryRows  = {summary_rows_js};
            const eccText      = {source_json};
            const eccId        = {source_id_json};

            (function buildTable() {{
                const tbody = document.getElementById("summary-tbody");
                summaryRows.forEach(function(row) {{
                    const tr = document.createElement("tr");
                    tr.onclick = function() {{ updatePanel("node_" + row.rank); }};
                    tr.innerHTML = `
                        <td><span class="rank-badge">${{row.rank}}</span></td>
                        <td style="font-weight:600;color:#1e293b;">${{escapeHtml(row.nist_control)}}</td>
                        <td>
                            <span style="display:inline-block;background:${{row.fill_color}};
                                color:white;border-radius:20px;padding:2px 9px;
                                font-weight:700;font-size:11px;">
                                ${{escapeHtml(row.final_percent)}}
                            </span>
                        </td>
                    `;
                    tbody.appendChild(tr);
                }});
            }})();

            function escapeHtml(text) {{
                if (!text) return "N/A";
                return String(text)
                    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;").replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            }}

            function showEccPanel() {{
                const panel = document.getElementById("detail-panel");
                panel.innerHTML = `
                    <div class="ecc-panel-header">
                        <div class="ecc-icon">🔵</div>
                        <div>
                            <div class="panel-title">ECC Control</div>
                            <div style="font-size:10px;color:#94a3b8;margin-top:1px;">Source control description</div>
                        </div>
                    </div>
                    <div class="sub-title">🏷️ Control ID</div>
                    <div class="content-box">
                        <b style="color:#4f46e5;font-size:13px;">${{escapeHtml(eccId)}}</b>
                    </div>
                    <div class="sub-title">📄 Description</div>
                    <div class="content-box" style="line-height:1.7;">${{escapeHtml(eccText)}}</div>
                    <div style="margin-top:10px;padding:8px 10px;border-radius:8px;
                                background:#eef2ff;border:1px solid #c7d2fe;
                                font-size:10px;color:#6366f1;font-weight:600;">
                        💡 Click any green node to view its NIST mapping details
                    </div>
                `;
            }}

            function updatePanel(nodeId) {{
                const item  = mappingData[nodeId];
                const panel = document.getElementById("detail-panel");
                if (!item) return;

                const finalVal   = parseFloat(item.final);
                const matchIcon  = finalVal >= 0.85 ? "🟢" : finalVal >= 0.70 ? "🟡" : "🔴";
                const matchLabel = finalVal >= 0.85 ? "High Match" : finalVal >= 0.70 ? "Medium Match" : "Low Match";

                const domain = item.nist_control.startsWith("GV") ? "Govern"
                             : item.nist_control.startsWith("ID") ? "Identify"
                             : item.nist_control.startsWith("PR") ? "Protect"
                             : item.nist_control.startsWith("DE") ? "Detect"
                             : item.nist_control.startsWith("RS") ? "Respond"
                             : item.nist_control.startsWith("RC") ? "Recover" : "Unknown";

                const fillColor = item.fill_color;

                panel.innerHTML = `
                    <div class="panel-header">
                        <div class="panel-rank-badge"
                             style="background:linear-gradient(135deg,${{fillColor}},${{fillColor}}cc);">
                            ${{item.rank}}
                        </div>
                        <div>
                            <div class="panel-title">Mapping #${{item.rank}} Details</div>
                            <div style="font-size:10px;color:#94a3b8;margin-top:1px;">
                                ${{escapeHtml(item.nist_control)}}
                            </div>
                        </div>
                    </div>

                    <div class="score-grid">
                        <div class="score-card score-card-main">
                            <div class="score-card-label">Final Match Score</div>
                            <div class="score-card-value">${{escapeHtml(item.final_percent)}}</div>
                            <div class="score-card-sub">${{escapeHtml(item.final)}} · ${{domain}}</div>
                        </div>
                        <div class="score-card score-card-embed">
                            <div class="score-card-label">Embedding</div>
                            <div class="score-card-value">${{escapeHtml(item.embedding_percent)}}</div>
                            <div class="score-card-sub">${{escapeHtml(item.embedding)}}</div>
                        </div>
                        <div class="score-card score-card-onto">
                            <div class="score-card-label">Ontology</div>
                            <div class="score-card-value">${{escapeHtml(item.ontology_percent)}}</div>
                            <div class="score-card-sub">${{escapeHtml(item.ontology)}}</div>
                        </div>
                    </div>
                    <div class="confidence-row">
                        ${{matchIcon}} <b>Confidence:</b> ${{matchLabel}}
                    </div>

                    <div class="sub-title">🎯 NIST Control</div>
                    <div class="content-box">
                        <b>${{escapeHtml(item.nist_control)}}</b><br><br>
                        ${{escapeHtml(item.nist_text)}}
                    </div>

                    <div class="sub-title">🤝 Commonality</div>
                    <div class="content-box">${{escapeHtml(item.commonality)}}</div>

                    <div class="sub-title">✅ Justification</div>
                    <div class="content-box">${{escapeHtml(item.justification)}}</div>

                    <div class="sub-title">⚡ Differences</div>
                    <div class="content-box">${{escapeHtml(item.differences)}}</div>
                `;
            }}
        </script>
    </body>
    </html>
    """
    return html_code


# ─────────────────────────────────────────
# Main app
# ─────────────────────────────────────────
DATA_FILE = "final_with_explanations_COMPLETE.csv"

if os.path.exists(DATA_FILE):

    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    if "ECC id control" not in df.columns:
        st.error("Column 'ECC id control' was not found in the CSV file.")
        st.stop()

    st.sidebar.title("ECC Controls")

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

    with st.sidebar.expander("🔍 Debug: CSV columns"):
        st.write("**All columns in CSV:**")
        for c in df.columns:
            st.write(f"• `{c}`")
        row_debug = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
        st.write("---")
        for mapping_num, targets in [
            (1, [("Final Score",     "Final Score"),
                 ("Embedding Score", "Embedding Score"),
                 ("Ontology Score",  "Ontology Score")]),
            (2, [("Final Score 2",     "Final Score 2"),
                 ("Embedding Score 2", "Embedding Score 2"),
                 ("Ontology Score 2",  "Ontology Score 2")]),
        ]:
            st.write(f"**Score column lookup for mapping {mapping_num}:**")
            for label, target in targets:
                found = find_col(list(df.columns), target)
                if found:
                    raw_val = row_debug.get(found, "N/A")
                    st.success(f"✅ `{target}` → `{found}` = `{raw_val}`")
                else:
                    st.error(f"❌ `{target}` → NOT FOUND")
            st.write("---")

    row             = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    source_text_col = find_col(list(df.columns), "Source Text")
    source_text     = safe_value(row.get(source_text_col, "") if source_text_col else "")

    # ── Header (no top margin/padding) ──────────────────────────────────
    header_col1, header_col2 = st.columns([4, 1.4])

    with header_col1:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg,#0f172a 0%,#312e81 60%,#4c1d95 100%);
                border-radius: 12px 0 0 12px;
                padding: 20px 28px;
                min-height: 110px;
                display: flex; flex-direction: column; justify-content: center;
                margin-left: -16px;
            ">
                <div style="font-size:11px;font-weight:600;color:#a5b4fc;
                            text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">
                    ECC–NIST Framework
                </div>
                <h1 style="margin:0;font-size:26px;color:#f8fafc;
                           font-family:'Inter',Arial,sans-serif;
                           font-weight:800;line-height:1.2;">
                    Control Mapping Viewer
                </h1>
                <p style="margin-top:8px;color:#94a3b8;font-size:13px;
                          font-family:'Inter',Arial,sans-serif;">
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
                background: linear-gradient(135deg,#0f172a 0%,#1e1b4b 100%);
                border: 1px solid #312e81;
                border-radius: 0 12px 12px 0;
                padding: 16px 18px;
                min-height: 110px;
                display: flex; flex-direction: column; justify-content: center;
            ">
                <p style="margin:0 0 10px 0;font-weight:700;color:white;
                          font-size:12px;text-transform:uppercase;letter-spacing:0.5px;">
                    Top-K Mappings
                </p>
            </div>
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
        <div style="margin-top:6px;margin-bottom:8px;color:#64748b;font-size:13px;">
            Showing <b style="color:#6366f1;">{len(mappings)}</b> recommended mapping(s) for
            <b style="color:#4f46e5;">{selected_id}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    viewer_html = create_svg_viewer(
        selected_id=str(selected_id),
        source_text=source_text,
        mappings=mappings,
    )

    col_graph, col_status = st.columns([4, 1])

    with col_status:
        st.markdown(
            """
            <div style="background:linear-gradient(135deg,#0f172a,#1e1b4b);
                        border-radius:12px;padding:16px 14px;margin-bottom:8px;">
                <div style="font-size:11px;font-weight:700;color:#a5b4fc;
                            text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">
                    Processing Pipeline
                </div>
            </div>
            """,
            unsafe_allow_html=True,
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
            "Returning Top-K",
        ]

        completed = []
        for step in steps:
            completed.append(step)
            rows_html = "".join(
                f'<div style="font-size:12px;color:#86efac;padding:3px 0;">✅ {s}</div>'
                if s in completed
                else
                f'<div style="font-size:12px;color:#475569;padding:3px 0;">⬜ {s}</div>'
                for s in steps
            )
            pipeline_box.markdown(
                f'<div style="background:linear-gradient(135deg,#0f172a,#1e1b4b);'
                f'border-radius:12px;padding:12px 14px;">{rows_html}</div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.15)

    with col_graph:
        # top-row min-height 500 + some padding; detail is inside so no extra rows below graph
        components.html(viewer_html, height=520, scrolling=False)

    # ── Export PDF (only thing below the viewer) ──────────────────────
    st.markdown(
        """
        <div style="height:1px;
                    background:linear-gradient(90deg,#e8edff,#c7d2fe,#e8edff);
                    margin:14px 0 12px 0;"></div>
        <div style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:10px;">
            Export Mapping Report
        </div>
        """,
        unsafe_allow_html=True,
    )

    pdf_bytes = generate_pdf(selected_id, source_text, mappings)

    if pdf_bytes:
        st.download_button(
            label="⬇  Export PDF Report",
            data=pdf_bytes,
            file_name=f"{selected_id}_mapping_report.pdf",
            mime="application/pdf",
        )
    else:
        st.warning(
            "PDF export requires the `fpdf2` library. "
            "Install it with: `pip install fpdf2`"
        )

else:
    st.markdown(
        f"""
        <div style="
            background:#fef2f2; border:1px solid #fecaca;
            border-radius:10px; padding:24px; margin-top:30px;
        ">
            <div style="font-size:16px;font-weight:700;color:#991b1b;margin-bottom:8px;">
                ⚠️ Data file not found
            </div>
            <div style="color:#7f1d1d;font-size:14px;">
                Make sure <code>{DATA_FILE}</code> is in the same folder as
                <code>mapviewer.py</code>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
