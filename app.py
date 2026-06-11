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
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background: #0a1628; color: #e2e8f0; }

        section[data-testid="stSidebar"] {
            background: #07111f;
            border-right: 1px solid #1d2b3f;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding: 0.8rem 0.75rem 1rem;
        }
        section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
        .side-head {
            border: 1px solid #1d2b3f;
            border-radius: 6px;
            padding: 4px 8px;
            margin-bottom: 4px;
            background: linear-gradient(135deg,#0b1728 0%,#0f2f3a 100%);
        }
        .side-kicker {
            color: #67e8f9 !important;
            font-size: 9px;
            font-weight: 800;
            letter-spacing: 0.7px;
            text-transform: uppercase;
            margin-bottom: 0;
            margin-top: 0;
        }
        .side-title {
            color: #f8fafc !important;
            font-size: 14px;
            font-weight: 800;
            line-height: 1.1;
            margin-top: 1px;
            margin-bottom: 0;
        }
        .side-count {
            color: #8aa3b8 !important;
            font-size: 9px;
            margin: 1px 0 2px;
        }
        section[data-testid="stSidebar"] input[type="text"] {
            background: #0f1b2d !important; border: 1px solid #28415c !important;
            border-radius: 6px !important; color: #f1f5f9 !important;
            font-size: 11px !important; padding: 4px 6px !important;
            height: 26px !important;
        }
        section[data-testid="stSidebar"] input[type="text"]::placeholder { color: #64748b !important; font-size: 10px !important; }
        section[data-testid="stSidebar"] .stTextInput,
        section[data-testid="stSidebar"] .stRadio {
            margin-bottom: 0.15rem !important;
            margin-top: 0.1rem !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            max-height: calc(100vh - 160px);
            overflow-y: auto;
            gap: 0 !important;
            padding-right: 4px;
            scrollbar-width: thin;
            scrollbar-color: #28415c #07111f;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"]::-webkit-scrollbar { width: 4px; }
        section[data-testid="stSidebar"] div[role="radiogroup"]::-webkit-scrollbar-track { background: #07111f; }
        section[data-testid="stSidebar"] div[role="radiogroup"]::-webkit-scrollbar-thumb {
            background: #28415c;
            border-radius: 4px;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: 3px 5px !important;
            margin: 0 !important;
            border-radius: 4px !important;
            transition: background 0.15s ease !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: #102235 !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label div,
        section[data-testid="stSidebar"] div[role="radiogroup"] label p,
        section[data-testid="stSidebar"] div[role="radiogroup"] label span {
            font-size: 12px !important;
            font-weight: 600 !important;
            line-height: 1.3 !important;
            text-transform: none !important;
            letter-spacing: 0 !important;
            color: #d5e4f0 !important;
        }

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] label p {
            font-size: 11px !important; font-weight: 700 !important;
            text-transform: uppercase !important; letter-spacing: 0.9px !important;
            color: #7892a8 !important; margin-bottom: 4px !important;
            margin-top: 2px !important;
        }

        .main .block-container,
        .block-container,
        div[data-testid="stAppViewBlockContainer"] {
            padding: 0.65rem 1rem 1.25rem !important;
            margin-top: -15px !important;
            max-width: 1540px !important;
        }
        .main .block-container > div:first-child { margin-top: 0 !important; }

        .stDownloadButton button {
            background: linear-gradient(135deg,#0f766e,#2563eb) !important;
            color: white !important; border: none !important;
            border-radius: 8px !important; font-weight: 600 !important;
            font-size: 14px !important; padding: 10px 22px !important;
        }
        .stDownloadButton button:hover {
            background: linear-gradient(135deg,#0d9488,#1d4ed8) !important;
        }

        #MainMenu { visibility: hidden; }
        footer    { visibility: hidden; }
        header    { visibility: hidden; }

        .topk-card {
            background: linear-gradient(135deg,#0b1728,#0f2f3a);
            border: 1px solid #245064;
            border-radius: 8px;
            padding: 10px 12px 6px;
            min-height: 54px;
        }
        .topk-title {
            font-size: 10px;
            font-weight: 800;
            color: #ffffff !important;
            text-transform: uppercase;
            letter-spacing: 0.7px;
        }
        .topk-sub {
            font-size: 11px;
            color: #8bd3dd !important;
            margin-top: 3px;
        }
        .pipeline-card {
            background: linear-gradient(135deg,#0b1728,#103044);
            border: 1px solid #245064;
            border-radius: 8px;
            padding: 10px 12px 6px;
            min-height: 54px;
            margin-top: 10px;
        }
        .pipeline-title {
            font-size: 10px;
            font-weight: 800;
            color: #ffffff !important;
            text-transform: uppercase;
            letter-spacing: 0.7px;
        }
        .pipeline-sub {
            font-size: 11px;
            color: #8bd3dd !important;
            margin-top: 3px;
        }

        [data-testid="stSelectSlider"],
        [data-testid="stSlider"] {
            padding-top: 0 !important;
            margin-top: -8px !important;
        }
        [data-testid="stSelectSlider"] *,
        [data-testid="stSlider"] * {
            color: #ffffff !important;
        }
        [data-testid="stSelectSlider"] [data-testid="stTickBarMin"],
        [data-testid="stSelectSlider"] [data-testid="stTickBarMax"],
        [data-testid="stSlider"] [data-testid="stTickBarMin"],
        [data-testid="stSlider"] [data-testid="stTickBarMax"],
        [data-testid="stSelectSlider"] [data-testid*="TickBar"],
        [data-testid="stSlider"] [data-testid*="TickBar"] {
            color: #ffffff !important;
            fill: #ffffff !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }
        [data-testid="stSelectSlider"] [data-testid*="TickBar"] *,
        [data-testid="stSlider"] [data-testid*="TickBar"] *,
        [data-testid="stSelectSlider"] svg text,
        [data-testid="stSelectSlider"] svg tspan,
        [data-testid="stSlider"] svg text,
        [data-testid="stSlider"] svg tspan,
        [data-testid="stThumbValue"],
        [data-testid="stThumbValue"] * {
            color: #ffffff !important;
            fill: #ffffff !important;
            opacity: 1 !important;
        }
        [data-testid="stSelectSlider"] [role="slider"] {
            background: #67e8f9 !important;
            border-color: #ffffff !important;
            box-shadow: 0 0 0 2px rgba(103,232,249,0.18) !important;
        }

        /* Hide sidebar collapse/expand button (sidebar icon button) */
        button[aria-label="More options"],
        button[aria-label="View fullscreen"],
        button[data-testid="stBaseButton-headerNoPadding"],
        button[data-testid="baseButton-secondary"],
        button[data-testid="icon-button"],
        button.icon-button {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
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
    def normalise(s): return re.sub(r"[\s_]+", "", s).lower()
    target_norm = normalise(target)
    for col in df_columns:
        if normalise(col) == target_norm:
            return col
    return None

def safe_get_score(row, df_columns, col_name):
    actual = find_col(df_columns, col_name)
    if actual is None: return 0.0
    return parse_score(row.get(actual, 0))

def natural_control_sort(value):
    value = str(value).strip()
    parts = re.split(r"[.\-_\s]+", value)
    return [int(p) if p.isdigit() else p for p in parts]

def safe_value(value, default="N/A"):
    if pd.isna(value) or str(value).strip() == "": return default
    return str(value).strip()

def parse_score(value):
    try:
        if pd.isna(value): return 0.0
        value = str(value).replace("%", "").strip()
        if value == "": return 0.0
        value = float(value)
        return value / 100.0 if value > 1 else value
    except: return 0.0

def format_decimal(score):
    try: return f"{float(score):.2f}"
    except: return "N/A"

def format_percent(score):
    try: return f"{int(round(float(score) * 100))}%"
    except: return "N/A"

def short_mapping_label(mapping):
    mapping = str(mapping).strip()
    if ":" in mapping:
        code, name = mapping.split(":", 1)
        code, name = code.strip(), name.strip()
        return code, (name[:11] + "…" if len(name) > 12 else name)
    parts = re.split(r"[-]", mapping)
    if len(parts) >= 2:
        number = "-".join(parts[:-1])
        name = parts[-1]
        return number, (name[:11] + "…" if len(name) > 12 else name)
    return (mapping[:9], mapping[9:]) if len(mapping) > 9 else (mapping, "")

def extract_mappings(row, df, top_k=5):
    results = []
    df_cols = list(df.columns)
    for i in range(1, 11):
        cols = get_mapping_columns(i)
        actual_mapping_col = find_col(df_cols, cols["mapping"])
        if actual_mapping_col is None: continue
        val = row.get(actual_mapping_col)
        if pd.isna(val) or str(val).strip() == "": continue
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
            "mapping": raw_mapping, "short_code": code, "short_name": name,
            "text":          safe_value(row.get(actual_text, "") if actual_text else ""),
            "final":         final_score,
            "embedding":     embedding_score,
            "ontology":      ontology_score,
            "commonality":   safe_value(row.get(actual_comm, "") if actual_comm else ""),
            "justification": safe_value(row.get(actual_just, "") if actual_just else ""),
            "differences":   safe_value(
                row.get(actual_diff, "") if actual_diff else "",
                "Controls differ in implementation focus and specific requirements."
            ),
        })
    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

def score_to_colors(score):
    if score >= 0.85:   return "#059669", "#34d399", "High Match",   "🟢"
    elif score >= 0.70: return "#d97706", "#fcd34d", "Medium Match", "🟡"
    else:               return "#dc2626", "#fca5a5", "Low Match",    "🔴"


# ─────────────────────────────────────────
# PDF Export
# ─────────────────────────────────────────
def generate_pdf(selected_id, source_text, mappings):
    try: from fpdf import FPDF
    except ImportError: return None
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
        pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(79, 70, 229)
        pdf.cell(0, 7, "ECC Control Description", ln=True)
        pdf.set_font("Helvetica", "", 10); pdf.set_text_color(55, 65, 81)
        pdf.multi_cell(0, 6, str(source_text).encode("latin-1","replace").decode("latin-1"))
        pdf.ln(4); pdf.set_draw_color(199,210,254); pdf.line(10,pdf.get_y(),200,pdf.get_y()); pdf.ln(5)
    for idx, m in enumerate(mappings):
        fv = float(m["final"])
        if fv >= 0.85:   conf, r, g, b = "High Match",   5,150,105
        elif fv >= 0.70: conf, r, g, b = "Medium Match", 217,119,6
        else:            conf, r, g, b = "Low Match",    220,38,38
        pdf.set_fill_color(r,g,b); pdf.set_text_color(255,255,255)
        pdf.set_font("Helvetica","B",12)
        pdf.cell(0,10,f"  #{idx+1}  {m['mapping']}  -  {format_percent(m['final'])}  ({conf})",ln=True,fill=True)
        pdf.ln(2)
        def field(label, value):
            pdf.set_font("Helvetica","B",10); pdf.set_text_color(79,70,229); pdf.cell(0,6,label,ln=True)
            pdf.set_font("Helvetica","",10); pdf.set_text_color(55,65,81)
            pdf.multi_cell(0,5.5,str(value).encode("latin-1","replace").decode("latin-1")); pdf.ln(2)
        pdf.set_font("Helvetica","B",10); pdf.set_text_color(79,70,229); pdf.cell(0,6,"Scores",ln=True)
        pdf.set_font("Helvetica","",10); pdf.set_text_color(55,65,81)
        pdf.cell(0,5.5,f"  Final:{format_percent(m['final'])}  Embedding:{format_percent(m['embedding'])}  Ontology:{format_percent(m['ontology'])}",ln=True)
        pdf.ln(2)
        field("NIST Control Text", m["text"])
        field("Commonality",       m["commonality"])
        field("Justification",     m["justification"])
        field("Differences",       m["differences"])
        pdf.set_draw_color(199,210,254); pdf.line(10,pdf.get_y(),200,pdf.get_y()); pdf.ln(5)
    return bytes(pdf.output())


# ─────────────────────────────────────────
# HTML Viewer
# ─────────────────────────────────────────
def create_viewer(selected_id, source_text, mappings):
    W, H     = 560, 420
    cx, cy   = 280, 210
    BR, GR   = 38, 32
    ORBIT    = 145

    svg_lines = svg_nodes = svg_nums = ""
    n = len(mappings)
    mapping_data = {}
    summary_rows = []

    for idx, item in enumerate(mappings):
        angle = (2 * math.pi / n) * idx - math.pi / 2
        x = cx + ORBIT * math.cos(angle)
        y = cy + ORBIT * math.sin(angle)
        rank   = idx + 1
        nid    = f"node_{rank}"
        col, badge, label, icon = score_to_colors(item["final"])
        pct    = format_percent(item["final"])
        code   = html.escape(item["short_code"])

        mapping_data[nid] = {
            "rank": str(rank), "nist_control": item["mapping"],
            "nist_text": item["text"],
            "final": format_decimal(item["final"]), "final_pct": pct,
            "emb": format_decimal(item["embedding"]), "emb_pct": format_percent(item["embedding"]),
            "ont": format_decimal(item["ontology"]),  "ont_pct": format_percent(item["ontology"]),
            "commonality": item["commonality"], "justification": item["justification"],
            "differences": item["differences"], "color": col, "icon": icon, "label": label,
            "domain": (
                "Govern" if item["mapping"].startswith("GV") else
                "Identify" if item["mapping"].startswith("ID") else
                "Protect" if item["mapping"].startswith("PR") else
                "Detect" if item["mapping"].startswith("DE") else
                "Respond" if item["mapping"].startswith("RS") else
                "Recover" if item["mapping"].startswith("RC") else "Unknown"
            ),
        }
        summary_rows.append({
            "rank": str(rank), "nist": item["mapping"],
            "pct": pct, "color": col,
        })

        dx, dy = x - cx, y - cy
        dist = math.sqrt(dx*dx + dy*dy)
        sx = cx + (BR / dist) * dx;  sy = cy + (BR / dist) * dy
        ex = x  - (GR / dist) * dx;  ey = y  - (GR / dist) * dy
        svg_lines += f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{col}" stroke-width="1.5" stroke-dasharray="5,3" opacity="0.55"/>\n'

        svg_nums += f'<text x="{x:.1f}" y="{y - GR - 8:.1f}" text-anchor="middle" fill="{col}" font-size="14" font-weight="800" font-family="Inter,sans-serif">#{rank}</text>\n'

        svg_nodes += f"""<g class="mnode" onclick="return selectNode({rank}, event)" data-rank="{rank}" data-color="{col}">
  <circle cx="{x:.1f}" cy="{y:.1f}" r="{GR+6}" fill="{col}" opacity="0.15" class="gring"/>
  <circle cx="{x:.1f}" cy="{y:.1f}" r="{GR}" fill="{col}"/>
  <text x="{x:.1f}" y="{y-8:.1f}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="16" font-weight="800" font-family="Inter,sans-serif">{code}</text>
  <text x="{x:.1f}" y="{y+10:.1f}" text-anchor="middle" dominant-baseline="middle" fill="rgba(255,255,255,0.9)" font-size="16" font-weight="700" font-family="Inter,sans-serif">{html.escape(pct)}</text>
</g>\n"""

    mdata_json   = json.dumps(mapping_data,  ensure_ascii=False)
    srows_json   = json.dumps(summary_rows,  ensure_ascii=False)
    src_json     = json.dumps(source_text,   ensure_ascii=False)
    src_id_json  = json.dumps(str(selected_id), ensure_ascii=False)
    n_mappings   = len(mappings)

    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link rel="stylesheet" href__="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{font-family:'Inter',sans-serif;background:#0a1628;color:#e2e8f0;min-height:100%;overflow:auto}}

.shell{{
  display:flex;width:100%;height:680px;min-height:680px;overflow:hidden;
  border:1px solid #1d2b3f;border-radius:12px;
  box-shadow:0 18px 42px rgba(0,0,0,0.22);
}}

.graph-col{{
  flex:0 0 58%;
  display:flex;flex-direction:column;
  background:radial-gradient(circle at 50% 40%,rgba(37,99,235,0.14),transparent 34%),
             linear-gradient(160deg,#0a1628 0%,#102a43 56%,#0f1e3d 100%);
  border-right:1px solid #1d2b3f;
  position:relative;overflow:hidden;
}}
.graph-header{{
  display:flex;align-items:center;gap:10px;
  padding:10px 16px 6px;
  border-bottom:1px solid #1d2b3f;
  flex-shrink:0;
}}
.graph-badge{{
  background:linear-gradient(135deg,#0f766e,#2563eb);
  color:white;font-size:9px;font-weight:700;letter-spacing:1px;
  text-transform:uppercase;padding:3px 10px;border-radius:20px;
}}
.graph-title{{font-size:13px;font-weight:700;color:#e2e8f0}}
.graph-subtitle{{font-size:11px;color:#8aa3b8;margin-top:1px}}
.svg-wrap{{flex:1;display:flex;align-items:center;justify-content:center;padding:8px 0 0}}
.svg-wrap svg{{width:min(100%,560px);height:auto;overflow:visible}}
.legend{{
  display:flex;gap:14px;padding:10px 18px 14px;
  border-top:1px solid #1d2b3f;flex-shrink:0;
}}
.leg{{display:flex;align-items:center;gap:5px;font-size:10px;font-weight:600;color:#8aa3b8}}
.legdot{{width:9px;height:9px;border-radius:50%;flex-shrink:0}}

.right-col{{
  flex:1;min-width:320px;display:flex;flex-direction:column;
  background:#0b1424;overflow:hidden;
}}

.tbl-section{{flex-shrink:0;border-bottom:1px solid #1d2b3f}}
.tbl-header{{padding:10px 16px 6px;background:#0b1424}}
.tbl-title{{font-size:12px;font-weight:700;color:#e2e8f0;display:flex;align-items:center;gap:6px}}
.tbl-sub{{font-size:10px;color:#6b8298;margin-top:1px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{
  background:linear-gradient(135deg,#0f766e,#2563eb);
  color:white;padding:8px 12px;text-align:left;
  font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;
}}
td{{padding:8px 12px;border-bottom:1px solid #1d2b3f;color:#cbd5e1;vertical-align:middle}}
tr:last-child td{{border-bottom:none}}
tr.trow:hover td{{background:#142337;cursor:pointer}}
tr.trow.active td{{background:#0f2f3a}}
.rbadge{{
  display:inline-flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,#14b8a6,#2563eb);
  color:white;border-radius:50%;width:20px;height:20px;
  font-weight:700;font-size:9px;
}}
.score-pill{{
  display:inline-block;color:white;border-radius:20px;
  padding:2px 9px;font-weight:700;font-size:10px;
}}

.detail-col{{
  flex:1;min-height:0;overflow-y:auto;padding:14px 16px 22px;
  scrollbar-width:thin;scrollbar-color:#28415c #0b1424;
  overscroll-behavior:contain;
}}
.detail-col::-webkit-scrollbar{{width:4px}}
.detail-col::-webkit-scrollbar-track{{background:#0b1424}}
.detail-col::-webkit-scrollbar-thumb{{background:#28415c;border-radius:4px}}

.placeholder{{
  color:#6b8298;font-size:12px;text-align:center;
  padding:28px 16px;border:1px dashed #28415c;
  border-radius:10px;margin-top:6px;line-height:1.8;
}}

.d-header{{display:flex;align-items:center;gap:10px;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid #1d2b3f}}
.d-rank{{
  width:28px;height:28px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:12px;font-weight:800;color:white;flex-shrink:0;
}}
.d-title{{font-size:14px;font-weight:700;color:#f1f5f9}}
.d-sub{{font-size:10px;color:#8aa3b8;margin-top:2px}}

.stitle{{
  font-size:9px;font-weight:700;color:#67e8f9;
  text-transform:uppercase;letter-spacing:0.8px;
  margin-top:10px;margin-bottom:3px;
}}
.cbox{{
  border:1px solid #1d2b3f;border-radius:8px;
  padding:8px 10px;font-size:11px;line-height:1.4;
  color:#a8bacb;background:#08111f;
  white-space:normal;
  display:inline-block;
}}

.sgrid{{display:grid;grid-template-columns:1fr 1fr;gap:6px}}
.scard{{border-radius:8px;padding:8px 10px;text-align:center}}
.scard.main{{background:linear-gradient(135deg,#0f766e,#2563eb);grid-column:1/-1}}
.scard.emb {{background:linear-gradient(135deg,#0369a1,#0891b2)}}
.scard.ont {{background:linear-gradient(135deg,#047857,#059669)}}
.slabel{{font-size:8px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px;color:rgba(255,255,255,0.7);margin-bottom:2px}}
.sval  {{font-size:18px;font-weight:800;color:white;line-height:1}}
.ssub  {{font-size:9px;color:rgba(255,255,255,0.6);margin-top:2px}}

.conf-row{{
  display:flex;align-items:center;gap:6px;margin-top:6px;
  padding:6px 10px;border-radius:8px;
  background:#08111f;border:1px solid #1d2b3f;
  font-size:11px;color:#a8bacb;font-weight:500;
}}

.mnode,.cnode{{cursor:pointer;pointer-events:all;transition:filter 0.15s ease,opacity 0.15s ease}}
.mnode circle,.cnode circle{{pointer-events:visiblePainted;transition:stroke 0.15s ease,opacity 0.15s ease,transform 0.15s ease}}
.mnode:hover .gring{{opacity:0.35!important}}
.mnode.selected .gring{{opacity:0.42!important}}
.mnode.selected circle:not(.gring){{stroke:white;stroke-width:2.5;vector-effect:non-scaling-stroke}}
.cnode:hover circle:first-child{{opacity:0.35!important}}
</style>
</head>
<body>
<div class="shell">

  <div class="graph-col">
    <div class="graph-header">
      <div>
        <div class="graph-badge">Control Mapping Graph</div>
      </div>
      <div style="margin-left:6px">
        <div class="graph-title">ECC–NIST Mapping</div>
        <div class="graph-subtitle">Click any node to inspect</div>
      </div>
    </div>

    <div class="svg-wrap">
      <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">
        <circle cx="{cx}" cy="{cy}" r="{ORBIT}"
                fill="none" stroke="#1e293b" stroke-width="1"
                stroke-dasharray="3,6"/>

        {svg_lines}

        <g class="cnode" onclick="return showEcc(event)">
          <circle cx="{cx}" cy="{cy}" r="{BR+12}" fill="#6366f1" opacity="0.12"/>
          <circle cx="{cx}" cy="{cy}" r="{BR}"
                  fill="url(#cgrad)" filter="drop-shadow(0 0 10px rgba(99,102,241,0.5))"/>
          <text x="{cx}" y="{cy-8}" text-anchor="middle" dominant-baseline="middle"
                fill="white" font-size="16" font-weight="800" font-family="Inter,sans-serif">{html.escape(str(selected_id))}</text>
          <text x="{cx}" y="{cy+10}" text-anchor="middle" dominant-baseline="middle"
                fill="rgba(255,255,255,0.5)" font-size="12" font-weight="700"
                font-family="Inter,sans-serif">click</text>
        </g>

        {svg_nodes}
        {svg_nums}

        <defs>
          <linearGradient id="cgrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%"   style="stop-color:#818cf8"/>
            <stop offset="100%" style="stop-color:#4f46e5"/>
          </linearGradient>
        </defs>
      </svg>
    </div>

    <div class="legend">
      <div class="leg"><div class="legdot" style="background:#059669"></div>High ≥85%</div>
      <div class="leg"><div class="legdot" style="background:#d97706"></div>Mid ≥70%</div>
      <div class="leg"><div class="legdot" style="background:#dc2626"></div>Low &lt;70%</div>
    </div>
  </div>

  <div class="right-col">

    <div class="tbl-section">
      <div class="tbl-header">
        <div class="tbl-title">📋 Results — <span style="color:#6366f1">{n_mappings} mapping(s)</span>&nbsp;for&nbsp;<b style="color:#818cf8">{html.escape(str(selected_id))}</b></div>
        <div class="tbl-sub">Click a row or node to view full details below</div>
      </div>
      <table>
        <thead><tr><th>#</th><th>NIST Control</th><th>Score</th></tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>

    <div class="detail-col" id="detail">
      <div class="placeholder">
        🔗 Select a node or row to view full mapping details<br>
        <span style="color:#334155;font-size:10px">Click the indigo ECC node for the source control</span>
      </div>
    </div>

  </div>
</div>

<script>
const MD   = {mdata_json};
const SR   = {srows_json};
const ECC_TEXT = {src_json};
const ECC_ID   = {src_id_json};
let activeRank = null;

SR.forEach(r => {{
  const tr = document.createElement("tr");
  tr.className = "trow";
  tr.dataset.rank = r.rank;
  tr.onclick = () => selectNode(parseInt(r.rank));
  tr.innerHTML = `
    <td><span class="rbadge">${{r.rank}}</span></td>
    <td style="font-weight:600;color:#e2e8f0;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${{esc(r.nist)}}</td>
    <td><span class="score-pill" style="background:${{r.color}}">${{r.pct}}</span></td>
  `;
  document.getElementById("tbody").appendChild(tr);
}});

function esc(t) {{
  if(!t) return "N/A";
  return String(t).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
                  .replace(/"/g,"&quot;").replace(/'/g,"&#039;");
}}

function setActive(rank) {{
  document.querySelectorAll(".trow").forEach(r => r.classList.remove("active"));
  const row = document.querySelector(`.trow[data-rank="${{rank}}"]`);
  if(row) row.classList.add("active");
  document.querySelectorAll(".mnode").forEach(g => g.classList.remove("selected"));
  const node = document.querySelector(`.mnode[data-rank="${{rank}}"]`);
  if(node) node.classList.add("selected");
  activeRank = rank;
}}

function selectNode(rank, event) {{
  if(event) {{
    event.preventDefault();
    event.stopPropagation();
  }}
  const item = MD[`node_${{rank}}`];
  if(!item) return false;
  setActive(rank);

  const detail = document.getElementById("detail");
  detail.innerHTML = `
    <div class="d-header">
      <div class="d-rank" style="background:${{item.color}}">${{item.rank}}</div>
      <div>
        <div class="d-title">Mapping #${{item.rank}} — ${{esc(item.nist_control)}}</div>
        <div class="d-sub">${{item.domain}} · ${{item.label}} ${{item.icon}}</div>
      </div>
    </div>

    <div class="sgrid">
      <div class="scard main">
        <div class="slabel">Final Match Score</div>
        <div class="sval">${{item.final_pct}}</div>
        <div class="ssub">${{item.final}} raw · ${{item.domain}}</div>
      </div>
      <div class="scard emb">
        <div class="slabel">Embedding</div>
        <div class="sval">${{item.emb_pct}}</div>
        <div class="ssub">${{item.emb}}</div>
      </div>
      <div class="scard ont">
        <div class="slabel">Ontology</div>
        <div class="sval">${{item.ont_pct}}</div>
        <div class="ssub">${{item.ont}}</div>
      </div>
    </div>
    <div class="conf-row">${{item.icon}} <b style="color:#e2e8f0">Confidence:</b> ${{item.label}}</div>

    <div class="stitle">🎯 NIST Control Text</div>
    <div class="cbox" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><b style="color:#818cf8">${{esc(item.nist_control)}}</b> ${{esc(item.nist_text)}}</div>

    <div class="stitle">🤝 Commonality</div>
    <div class="cbox" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${{esc(item.commonality)}}</div>

    <div class="stitle">✅ Justification</div>
    <div class="cbox" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${{esc(item.justification)}}</div>

    <div class="stitle">⚡ Differences</div>
    <div class="cbox" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${{esc(item.differences)}}</div>
  `;
  detail.scrollTop = 0;
  return false;
}}

function showEcc(event) {{
  if(event) {{
    event.preventDefault();
    event.stopPropagation();
  }}
  document.querySelectorAll(".mnode").forEach(g => g.classList.remove("selected"));
  document.querySelectorAll(".trow").forEach(r => r.classList.remove("active"));
  activeRank = null;

  document.getElementById("detail").innerHTML = `
    <div class="d-header">
      <div class="d-rank" style="background:linear-gradient(135deg,#6366f1,#4f46e5)">⬡</div>
      <div>
        <div class="d-title">ECC Control — ${{esc(ECC_ID)}}</div>
        <div class="d-sub">Source control description</div>
      </div>
    </div>
    <div class="stitle">🏷️ Control ID</div>
    <div class="cbox"><b style="color:#818cf8;font-size:14px">${{esc(ECC_ID)}}</b></div>
    <div class="stitle">📄 Description</div>
    <div class="cbox" style="line-height:1.4;white-space:normal;display:inline-block;">${{esc(ECC_TEXT)}}</div>
    <div style="margin-top:10px;padding:8px 10px;border-radius:8px;background:#0a0f1e;border:1px solid #1e293b;font-size:10px;color:#6366f1;font-weight:600">
      💡 Click any outer node to view its NIST mapping details
    </div>
  `;
  document.getElementById("detail").scrollTop = 0;
  return false;
}}
</script>
</body></html>"""


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

    # ── Sidebar: ECC Controls with search ──
    st.sidebar.markdown(
        """
        <div class="side-head">
          <div class="side-kicker">ECC Controls</div>
          <div class="side-title">Control Picker</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    search_term = st.sidebar.text_input("Search", placeholder="e.g. 1-1 or PR.AA", key="search_term")

    all_ids = sorted(df["ECC id control"].astype(str).unique(), key=natural_control_sort)
    filtered = [c for c in all_ids if search_term.strip().lower() in c.lower()] if search_term.strip() else all_ids
    if not filtered:
        st.sidebar.warning("No matches.")
        filtered = all_ids

    if "selected_id" not in st.session_state:
        st.session_state.selected_id = all_ids[0]

    exact = next((c for c in all_ids if c.lower() == search_term.strip().lower()), None)
    if exact and exact != st.session_state.selected_id:
        st.session_state.selected_id = exact

    default_idx = filtered.index(st.session_state.selected_id) if st.session_state.selected_id in filtered else 0
    selected_id = st.sidebar.radio(
        "Select Control ID",
        filtered,
        index=default_idx,
    )
    st.session_state.selected_id = selected_id
    st.sidebar.markdown(
        f'<div class="side-count">{len(filtered)} of {len(all_ids)} controls shown</div>',
        unsafe_allow_html=True,
    )

    if st.sidebar.checkbox("Show debug columns", value=False):
        for c in df.columns:
            st.sidebar.write(f"• `{c}`")

    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    src_col  = find_col(list(df.columns), "Source Text")
    src_text = safe_value(row.get(src_col, "") if src_col else "")

    st.markdown(
        f"""<div style="
            background:linear-gradient(135deg,#08111f 0%,#0f1e3d 58%,#162e63 100%);
            border:1px solid #245064;
            border-radius:10px;padding:12px 20px;
            display:flex;align-items:center;gap:18px;
            box-shadow:0 10px 30px rgba(0,0,0,0.18);
            margin-bottom:10px;margin-top:-5px;
        ">
          <div>
            <div style="font-size:10px;font-weight:700;color:#67e8f9;
                        text-transform:uppercase;letter-spacing:1px;">ECC–NIST Framework</div>
            <div style="font-size:20px;font-weight:800;color:#f8fafc;line-height:1.2;
                        font-family:'Inter',sans-serif;">Control Mapping Viewer</div>
            <div style="font-size:12px;color:#8aa3b8;margin-top:2px;">
              Active: <span style="color:#8bd3dd;font-weight:700;">{selected_id}</span>
            </div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Main viewer + right-side controls ──
    col_v, col_p = st.columns([4.4, 1.65])

    with col_p:
        # Top-K card + slider
        st.markdown(
            """<div class="topk-card">
              <div class="topk-title">Top-K</div>
              <div class="topk-sub">Mappings</div>
            </div>""",
            unsafe_allow_html=True,
        )
        top_k = st.select_slider(
            "Top-K",
            options=list(range(1, 6)),
            value=5,
            label_visibility="collapsed",
        )

        # Pipeline card stacked below Top-K
        st.markdown(
            """<div class="pipeline-card">
              <div class="pipeline-title">Pipeline</div>
              <div class="pipeline-sub">Status</div>
            </div>""",
            unsafe_allow_html=True,
        )
        pipe_box = st.empty()
        steps = [
            "Load ECC Control",
            "Load NIST Controls",
            "Extract Metadata",
            "Semantic Embeddings",
            "Ontology Scoring",
            "Confidence Match",
            "AI Explanation",
            "Return Top-K",
        ]
        completed = []
        for step in steps:
            completed.append(step)
            rows_html = "".join(
                f'<div style="font-size:11px;color:#86efac;padding:2px 0">✅ {s}</div>'
                if s in completed else
                f'<div style="font-size:11px;color:#334155;padding:2px 0">⬜ {s}</div>'
                for s in steps
            )
            pipe_box.markdown(
                f'<div style="background:linear-gradient(135deg,#0b1728,#103044);'
                f'border:1px solid #245064;border-radius:10px;padding:10px 12px;'
                f'margin-top:6px">{rows_html}</div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.12)

    mappings = extract_mappings(row, df, top_k=top_k)

    with col_v:
        viewer_html = create_viewer(str(selected_id), src_text, mappings)
        components.html(viewer_html, height=700, scrolling=True)

    # ── Export ──
    st.markdown(
        """<div style="height:1px;background:linear-gradient(90deg,#1e293b,#4f46e5,#1e293b);
                       margin:12px 0 10px"></div>
           <div style="font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:8px;">
             Export Mapping Report
           </div>""",
        unsafe_allow_html=True,
    )

    pdf_bytes = generate_pdf(selected_id, src_text, mappings)
    if pdf_bytes:
        st.download_button(
            label="⬇  Export PDF Report",
            data=pdf_bytes,
            file_name=f"{selected_id}_mapping_report.pdf",
            mime="application/pdf",
        )
    else:
        st.warning("PDF export requires `fpdf2` — install with: `pip install fpdf2`")

else:
    st.markdown(
        f"""<div style="background:#1e293b;border:1px solid #dc2626;border-radius:10px;
                        padding:24px;margin-top:30px;">
          <div style="font-size:16px;font-weight:700;color:#fca5a5;margin-bottom:8px;">
            ⚠️ Data file not found
          </div>
          <div style="color:#94a3b8;font-size:14px;">
            Make sure <code style="color:#818cf8">{DATA_FILE}</code> is in the same folder.
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
