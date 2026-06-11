import streamlit as st
import urllib.parse
import pandas as pd
import streamlit.components.v1 as components
import os
import math
import json
import html
import re
import time
import base64

st.set_page_config(page_title="ECC-NIST Control Mapping Viewer", layout="wide")

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background: #08111f; color: #e2e8f0; }

        section[data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"],
        div[data-testid="stSidebarCollapsedControl"],
        button[aria-label="Open sidebar"],
        button[aria-label="Close sidebar"],
        .st-emotion-cache-1dp5vir { display: none !important; visibility: hidden !important; }

        .main .block-container,
        .block-container,
        div[data-testid="stAppViewBlockContainer"] {
            padding: 0.65rem 1rem 1.25rem !important;
            margin-top: 0 !important;
            max-width: 1540px !important;
        }
        .main .block-container > div:first-child { margin-top: 0 !important; }

        /* Responsive: on small screens, stack columns */
        /* ── Responsive: phone & tablet ── */
        @media (max-width: 768px) {
            .main .block-container,
            .block-container,
            div[data-testid="stAppViewBlockContainer"] {
                padding: 0.3rem 0.3rem 1rem !important;
            }
            /* Stack columns vertically on mobile */
            div[data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
                gap: 8px !important;
            }
            div[data-testid="stHorizontalBlock"] > div {
                width: 100% !important;
                min-width: 0 !important;
                flex: none !important;
            }
            /* Make header wrap nicely */
            div[data-testid="stAppViewBlockContainer"] > div:first-child div {
                font-size: 16px !important;
            }
            /* Download button full width */
            .stDownloadButton button {
                font-size: 13px !important;
                padding: 8px 14px !important;
            }
        }
        @media (max-width: 480px) {
            .main .block-container,
            .block-container,
            div[data-testid="stAppViewBlockContainer"] {
                padding: 0.2rem 0.2rem 0.8rem !important;
            }
        }

        .stDownloadButton button {
            background: linear-gradient(135deg,#0f766e,#2563eb) !important;
            color: white !important; border: none !important;
            border-radius: 8px !important; font-weight: 600 !important;
            font-size: 14px !important; padding: 10px 22px !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
        }
        .stDownloadButton button:hover {
            background: linear-gradient(135deg,#0d9488,#1d4ed8) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 15px rgba(20,184,166,0.3) !important;
        }

        #MainMenu { visibility: hidden; }
        footer    { visibility: hidden; }
        header    { visibility: hidden; }



        div[data-testid="stTextInput"] input {
            background: #0f1b2d !important; border: 1px solid #28415c !important;
            border-radius: 8px !important; color: #f1f5f9 !important;
            font-size: 13px !important; padding: 7px 10px !important;
        }
        div[data-testid="stTextInput"] input::placeholder { color: #64748b !important; }

        /* ECC control list — rendered as custom HTML component */

        /* Top-K card */
        .topk-card {
            background: linear-gradient(135deg,#0b1728,#0f2f3a);
            border: 1px solid #245064; border-radius: 8px;
            padding: 10px 12px 6px; min-height: 54px;
        }
        .topk-title { font-size: 10px; font-weight: 800; color: #ffffff !important;
            text-transform: uppercase; letter-spacing: 0.7px; }
        .topk-sub { font-size: 11px; color: #8bd3dd !important; margin-top: 3px; }

        /* Workflow card — replaces pipeline, clearly labelled as static */
        .workflow-card {
            background: linear-gradient(135deg,#0b1728,#103044);
            border: 1px solid #245064; border-radius: 8px;
            padding: 10px 12px 6px; min-height: 54px; margin-top: 10px;
        }
        .workflow-title { font-size: 10px; font-weight: 800; color: #ffffff !important;
            text-transform: uppercase; letter-spacing: 0.7px; }
        .workflow-sub { font-size: 11px; color: #64748b !important; margin-top: 3px; }

        /* ECC description card */
        .ecc-desc-card {
            background: linear-gradient(135deg,#0b1a2e,#0e2a40);
            border: 1px solid #245064; border-radius: 10px;
            padding: 14px 16px 12px; margin-bottom: 10px;
        }
        .ecc-desc-label {
            font-size: 9px; font-weight: 800; color: #67e8f9;
            text-transform: uppercase; letter-spacing: 0.9px; margin-bottom: 6px;
        }
        .ecc-desc-id {
            font-size: 16px; font-weight: 800; color: #818cf8;
            margin-bottom: 4px; line-height: 1.2;
        }
        .ecc-desc-text {
            font-size: 12px; color: #94a3b8; line-height: 1.75;
        }

        /* Preview image card */
        .preview-card {
            background: #060e1c;
            border: 1px solid #1d2b3f; border-radius: 10px;
            overflow: hidden; margin-bottom: 10px;
        }
        .preview-label {
            font-size: 9px; font-weight: 800; color: #67e8f9;
            text-transform: uppercase; letter-spacing: 0.9px;
            padding: 8px 12px 4px;
        }
        .preview-card img {
            width: 100%; display: block;
            border-radius: 0 0 10px 10px;
        }

        [data-testid="stSelectSlider"],
        [data-testid="stSlider"] { padding-top: 0 !important; margin-top: -8px !important; }
        [data-testid="stSelectSlider"] *, [data-testid="stSlider"] * { color: #ffffff !important; }
        [data-testid="stSelectSlider"] [role="slider"] {
            background: #67e8f9 !important; border-color: #ffffff !important;
            box-shadow: 0 0 0 2px rgba(103,232,249,0.18) !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------
# Helpers
# -----------------------------------------
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
        return code, (name[:11] + "..." if len(name) > 12 else name)
    parts = re.split(r"[-]", mapping)
    if len(parts) >= 2:
        number = "-".join(parts[:-1])
        name = parts[-1]
        return number, (name[:11] + "..." if len(name) > 12 else name)
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
    if score >= 0.85:   return "#059669", "#34d399", "High Match",   "green"
    elif score >= 0.70: return "#d97706", "#fcd34d", "Medium Match", "yellow"
    else:               return "#dc2626", "#fca5a5", "Low Match",    "red"


# -----------------------------------------
# PDF Export
# -----------------------------------------
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


# -----------------------------------------
# HTML Viewer — graph left, detail right (ECC desc shown by default)
# -----------------------------------------
def create_viewer(selected_id, source_text, mappings):
    W, H   = 480, 400
    cx, cy = 240, 200
    BR, GR = 36, 30
    ORBIT  = 130

    svg_lines = svg_nodes = svg_nums = ""
    n = len(mappings)
    mapping_data = {}

    for idx, item in enumerate(mappings):
        angle = (2 * math.pi / n) * idx - math.pi / 2
        x = cx + ORBIT * math.cos(angle)
        y = cy + ORBIT * math.sin(angle)
        rank  = idx + 1
        nid   = f"node_{rank}"
        col, badge, label, icon = score_to_colors(item["final"])
        pct   = format_percent(item["final"])
        code  = html.escape(item["short_code"])

        mapping_data[nid] = {
            "rank": str(rank), "nist_control": item["mapping"],
            "nist_text": item["text"],
            "final": format_decimal(item["final"]), "final_pct": pct,
            "emb": format_decimal(item["embedding"]), "emb_pct": format_percent(item["embedding"]),
            "ont": format_decimal(item["ontology"]),  "ont_pct": format_percent(item["ontology"]),
            "commonality": item["commonality"], "justification": item["justification"],
            "differences": item["differences"], "color": col, "icon": icon, "label": label,
            "domain": (
                "Govern"   if item["mapping"].startswith("GV") else
                "Identify" if item["mapping"].startswith("ID") else
                "Protect"  if item["mapping"].startswith("PR") else
                "Detect"   if item["mapping"].startswith("DE") else
                "Respond"  if item["mapping"].startswith("RS") else
                "Recover"  if item["mapping"].startswith("RC") else "Unknown"
            ),
        }

        dx, dy = x - cx, y - cy
        dist = math.sqrt(dx*dx + dy*dy)
        sx = cx + (BR / dist) * dx;  sy = cy + (BR / dist) * dy
        ex = x  - (GR / dist) * dx;  ey = y  - (GR / dist) * dy
        svg_lines += f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{col}" stroke-width="1.5" stroke-dasharray="5,3" opacity="0.55"/>\n'
        svg_nums  += f'<text x="{x:.1f}" y="{y - GR - 8:.1f}" text-anchor="middle" fill="{col}" font-size="10" font-weight="700" font-family="Inter,sans-serif">#{rank}</text>\n'
        svg_nodes += f"""<g class="mnode" onclick="return selectNode({rank}, event)" data-rank="{rank}" data-color="{col}">
  <circle cx="{x:.1f}" cy="{y:.1f}" r="{GR+6}" fill="{col}" opacity="0.15" class="gring"/>
  <circle cx="{x:.1f}" cy="{y:.1f}" r="{GR}" fill="{col}"/>
  <text x="{x:.1f}" y="{y-7:.1f}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="12" font-weight="800" font-family="Inter,sans-serif">{code}</text>
  <text x="{x:.1f}" y="{y+8:.1f}" text-anchor="middle" dominant-baseline="middle" fill="rgba(255,255,255,0.9)" font-size="11" font-weight="700" font-family="Inter,sans-serif">{html.escape(pct)}</text>
</g>\n"""

    mdata_json  = json.dumps(mapping_data, ensure_ascii=False)
    src_json    = json.dumps(source_text,  ensure_ascii=False)
    src_id_json = json.dumps(str(selected_id), ensure_ascii=False)

    # Build the default ECC description HTML shown on load
    ecc_desc_escaped = html.escape(source_text) if source_text and source_text != "N/A" else \
        '<span style="color:#475569;font-style:italic">No description available.</span>'

    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{font-family:'Inter',sans-serif;background:#08111f;color:#e2e8f0;overflow:hidden;height:100%}}

/* ── outer shell ── */
.shell{{
  display:flex;width:100%;height:100vh;
  border:1px solid #1d2b3f;border-radius:12px;
  box-shadow:0 18px 42px rgba(0,0,0,0.22);
  overflow:hidden;
}}

/* ── graph column (left, narrower) ── */
.graph-col{{
  flex:0 0 50%;
  display:flex;flex-direction:column;
  background:radial-gradient(circle at 50% 42%,rgba(20,184,166,0.13),transparent 32%),
             linear-gradient(160deg,#08111f 0%,#102a43 56%,#062f3a 100%);
  border-right:1px solid #1d2b3f;
  overflow:hidden;
}}
.graph-header{{
  display:flex;align-items:center;gap:10px;
  padding:12px 16px 10px;
  border-bottom:1px solid #1d2b3f;flex-shrink:0;
}}
.graph-badge{{
  background:linear-gradient(135deg,#0f766e,#2563eb);
  color:white;font-size:9px;font-weight:700;letter-spacing:1px;
  text-transform:uppercase;padding:3px 9px;border-radius:20px;
}}
.graph-title{{font-size:13px;font-weight:700;color:#e2e8f0}}
.graph-subtitle{{font-size:10px;color:#8aa3b8;margin-top:1px}}
.svg-wrap{{
  flex:1;display:flex;align-items:center;justify-content:center;
  padding:4px 0;min-height:0;
}}
.svg-wrap svg{{width:100%;max-width:{W}px;height:auto;overflow:visible}}
.legend{{
  display:flex;gap:12px;padding:8px 16px 12px;
  border-top:1px solid #1d2b3f;flex-shrink:0;
}}
.leg{{display:flex;align-items:center;gap:5px;font-size:10px;font-weight:600;color:#8aa3b8}}
.legdot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}

/* ── detail column (right, wider) ── */
.right-col{{
  flex:1;min-width:0;
  display:flex;flex-direction:column;
  background:#0b1424;overflow:hidden;
}}
.detail-header{{
  padding:12px 16px 8px;
  border-bottom:1px solid #1d2b3f;flex-shrink:0;
  display:flex;align-items:center;justify-content:space-between;
}}
.detail-h-title{{font-size:12px;font-weight:700;color:#e2e8f0}}
.detail-h-sub{{font-size:10px;color:#6b8298;margin-top:2px}}
.back-btn{{
  font-size:10px;font-weight:600;color:#67e8f9;
  background:none;border:1px solid #245064;border-radius:6px;
  padding:3px 8px;cursor:pointer;display:none;
  transition:background 0.15s;
}}
.back-btn:hover{{background:#0d2034}}

.detail-col{{
  flex:1;min-height:0;overflow-y:auto;
  padding:14px 16px 22px;
  scrollbar-width:thin;scrollbar-color:#28415c #0b1424;
  overscroll-behavior:contain;
}}
.detail-col::-webkit-scrollbar{{width:4px}}
.detail-col::-webkit-scrollbar-track{{background:#0b1424}}
.detail-col::-webkit-scrollbar-thumb{{background:#28415c;border-radius:4px}}

/* ── ECC description default view ── */
.ecc-default{{}}
.ecc-ctrl-id{{
  font-size:18px;font-weight:800;color:#818cf8;
  margin-bottom:6px;line-height:1.2;
}}
.ecc-ctrl-label{{
  font-size:9px;font-weight:700;color:#67e8f9;
  text-transform:uppercase;letter-spacing:0.9px;margin-bottom:10px;
}}
.ecc-desc-box{{
  border:1px solid #1d2b3f;border-radius:8px;
  padding:10px 12px;font-size:12px;line-height:1.8;
  color:#a8bacb;background:#08111f;
}}
.ecc-hint{{
  margin-top:12px;padding:8px 12px;border-radius:8px;
  background:#0a0f1e;border:1px solid #1e293b;
  font-size:10px;color:#6366f1;font-weight:600;
}}

/* ── mapping detail view ── */
.d-header{{display:flex;align-items:center;gap:10px;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid #1d2b3f}}
.d-rank{{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:white;flex-shrink:0;}}
.d-title{{font-size:13px;font-weight:700;color:#f1f5f9;line-height:1.3}}
.d-sub{{font-size:10px;color:#8aa3b8;margin-top:2px}}
.stitle{{font-size:9px;font-weight:700;color:#67e8f9;text-transform:uppercase;letter-spacing:0.8px;margin-top:10px;margin-bottom:3px;}}
.cbox{{border:1px solid #1d2b3f;border-radius:8px;padding:8px 10px;font-size:11px;line-height:1.6;color:#a8bacb;background:#08111f;white-space:pre-wrap;word-break:break-word;}}
.sgrid{{display:grid;grid-template-columns:1fr 1fr;gap:6px}}
.scard{{border-radius:8px;padding:8px 10px;text-align:center}}
.scard.main{{background:linear-gradient(135deg,#0f766e,#2563eb);grid-column:1/-1}}
.scard.emb{{background:linear-gradient(135deg,#0369a1,#0891b2)}}
.scard.ont{{background:linear-gradient(135deg,#047857,#059669)}}
.slabel{{font-size:8px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px;color:rgba(255,255,255,0.7);margin-bottom:2px}}
.sval{{font-size:18px;font-weight:800;color:white;line-height:1}}
.ssub{{font-size:9px;color:rgba(255,255,255,0.6);margin-top:2px}}
.conf-row{{display:flex;align-items:center;gap:6px;margin-top:6px;padding:6px 10px;border-radius:8px;background:#08111f;border:1px solid #1d2b3f;font-size:11px;color:#a8bacb;font-weight:500;}}

/* ── node interaction ── */
.mnode,.cnode{{cursor:pointer;pointer-events:all;transition:filter 0.15s ease}}
.mnode circle,.cnode circle{{pointer-events:visiblePainted;transition:stroke 0.15s ease,opacity 0.15s ease}}
.mnode:hover .gring{{opacity:0.35!important}}
.mnode.selected .gring{{opacity:0.42!important}}
.mnode.selected circle:not(.gring){{stroke:white;stroke-width:2.5;vector-effect:non-scaling-stroke}}
.cnode:hover circle:first-child{{opacity:0.35!important}}

/* ── responsive ── */
@media (max-width:680px){{
  .shell{{flex-direction:column;height:auto}}
  .graph-col{{flex:none}}
  .svg-wrap{{padding:8px}}
  .right-col{{min-height:360px}}
}}
</style>
</head>
<body>
<div class="shell">

  <!-- ── Graph panel (left) ── -->
  <div class="graph-col">
    <div class="graph-header">
      <div><div class="graph-badge">Mapping Graph</div></div>
      <div style="margin-left:6px">
        <div class="graph-title">ECC-NIST</div>
        <div class="graph-subtitle">Click a node to inspect</div>
      </div>
    </div>
    <div class="svg-wrap">
      <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">
        <circle cx="{cx}" cy="{cy}" r="{ORBIT}" fill="none" stroke="#1e293b" stroke-width="1" stroke-dasharray="3,6"/>
        {svg_lines}
        <g class="cnode" onclick="return showEcc(event)">
          <circle cx="{cx}" cy="{cy}" r="{BR+12}" fill="#6366f1" opacity="0.12"/>
          <circle cx="{cx}" cy="{cy}" r="{BR}" fill="url(#cgrad)" filter="drop-shadow(0 0 10px rgba(99,102,241,0.5))"/>
          <text x="{cx}" y="{cy-9}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="13" font-weight="800" font-family="Inter,sans-serif">ECC</text>
          <text x="{cx}" y="{cy+8}" text-anchor="middle" dominant-baseline="middle" fill="rgba(255,255,255,0.8)" font-size="10" font-weight="700" font-family="Inter,sans-serif">{html.escape(str(selected_id))}</text>
          <text x="{cx}" y="{cy+21}" text-anchor="middle" dominant-baseline="middle" fill="rgba(255,255,255,0.35)" font-size="8" font-family="Inter,sans-serif">click</text>
        </g>
        {svg_nodes}
        {svg_nums}
        <defs>
          <linearGradient id="cgrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#818cf8"/>
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

  <!-- ── Detail panel (right) ── -->
  <div class="right-col">
    <div class="detail-header">
      <div>
        <div class="detail-h-title" id="panel-title">ECC Control</div>
        <div class="detail-h-sub" id="panel-sub">Click a node for mapping details</div>
      </div>
      <button class="back-btn" id="back-btn" onclick="showEcc()">← Back</button>
    </div>
    <div class="detail-col" id="detail">
      <!-- Default: ECC description shown immediately on load -->
      <div class="ecc-default">
        <div class="ecc-ctrl-label">ECC Source Control</div>
        <div class="ecc-ctrl-id">{html.escape(str(selected_id))}</div>
        <div class="stitle">Description</div>
        <div class="ecc-desc-box">{ecc_desc_escaped}</div>
        <div class="ecc-hint">Click any outer node to view its NIST mapping details</div>
      </div>
    </div>
  </div>

</div>
<script>
const MD       = {mdata_json};
const ECC_TEXT = {src_json};
const ECC_ID   = {src_id_json};
let activeRank = null;

function esc(t) {{
  if (!t) return "N/A";
  return String(t)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");
}}

function setPanelHeader(title, sub, showBack) {{
  document.getElementById("panel-title").textContent = title;
  document.getElementById("panel-sub").textContent   = sub;
  document.getElementById("back-btn").style.display  = showBack ? "block" : "none";
}}

function setActive(rank) {{
  document.querySelectorAll(".mnode").forEach(g => g.classList.remove("selected"));
  const node = document.querySelector(`.mnode[data-rank="${{rank}}"]`);
  if (node) node.classList.add("selected");
  activeRank = rank;
}}

function selectNode(rank, event) {{
  if (event) {{ event.preventDefault(); event.stopPropagation(); }}
  const item = MD[`node_${{rank}}`];
  if (!item) return false;
  setActive(rank);
  setPanelHeader(`Mapping #${{item.rank}} — ${{item.domain}}`, `${{item.label}} · ${{item.final_pct}}`, true);
  const detail = document.getElementById("detail");
  detail.innerHTML = `
    <!-- ECC description pinned at top -->
    <div style="border:1px solid #1d2b3f;border-radius:8px;padding:10px 12px;background:#08111f;margin-bottom:14px;">
      <div style="font-size:9px;font-weight:700;color:#67e8f9;text-transform:uppercase;letter-spacing:0.9px;margin-bottom:4px;">ECC Source Control</div>
      <div style="font-size:14px;font-weight:800;color:#818cf8;margin-bottom:6px;line-height:1.2;">${{esc(ECC_ID)}}</div>
      <div style="font-size:11px;line-height:1.7;color:#7a90a8;">${{esc(ECC_TEXT)}}</div>
    </div>
    <!-- divider -->
    <div style="height:1px;background:linear-gradient(90deg,#1e293b,#4f46e5,#1e293b);margin-bottom:12px;"></div>
    <!-- NIST mapping detail -->
    <div class="d-header">
      <div class="d-rank" style="background:${{item.color}}">${{item.rank}}</div>
      <div>
        <div class="d-title">${{esc(item.nist_control)}}</div>
        <div class="d-sub">${{item.domain}} · ${{item.label}}</div>
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
    <div class="conf-row"><b style="color:#e2e8f0">Confidence:</b>&nbsp;${{item.label}}</div>
    <div class="stitle">NIST Control Text</div>
    <div class="cbox"><b style="color:#818cf8">${{esc(item.nist_control)}}</b>&#10;&#10;${{esc(item.nist_text)}}</div>
    <div class="stitle">Commonality</div>
    <div class="cbox">${{esc(item.commonality)}}</div>
    <div class="stitle">Justification</div>
    <div class="cbox">${{esc(item.justification)}}</div>
    <div class="stitle">Differences</div>
    <div class="cbox">${{esc(item.differences)}}</div>
  `;
  detail.scrollTop = 0;
  return false;
}}

function showEcc(event) {{
  if (event) {{ event.preventDefault(); event.stopPropagation(); }}
  document.querySelectorAll(".mnode").forEach(g => g.classList.remove("selected"));
  activeRank = null;
  setPanelHeader("ECC Control", "Click a node for mapping details", false);
  const detail = document.getElementById("detail");
  detail.innerHTML = `
    <div class="ecc-default">
      <div class="ecc-ctrl-label">ECC Source Control</div>
      <div class="ecc-ctrl-id">${{esc(ECC_ID)}}</div>
      <div class="stitle">Description</div>
      <div class="ecc-desc-box">${{esc(ECC_TEXT)}}</div>
      <div class="ecc-hint">Click any outer node to view its NIST mapping details</div>
    </div>
  `;
  detail.scrollTop = 0;
  return false;
}}
</script>
</body></html>"""


# -----------------------------------------
# Main app
# -----------------------------------------
DATA_FILE = "final_with_explanations_COMPLETE.csv"

# Load the preview image as base64 for embedding
_PREVIEW_IMG_B64 = ""
_PREVIEW_IMG_PATH = os.path.join(os.path.dirname(__file__), "mapping_preview.png")
if os.path.exists(_PREVIEW_IMG_PATH):
    with open(_PREVIEW_IMG_PATH, "rb") as _f:
        _PREVIEW_IMG_B64 = base64.b64encode(_f.read()).decode()

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    if "ECC id control" not in df.columns:
        st.error("Column 'ECC id control' was not found in the CSV file.")
        st.stop()

    all_ids = sorted(df["ECC id control"].astype(str).unique(), key=natural_control_sort)

    if "selected_id" not in st.session_state:
        st.session_state.selected_id = all_ids[0]

    # ── Handle grid pill click — query param triggers rerun ─────────────────
    _qp = st.query_params
    if "ctrl_pick" in _qp:
        _picked = _qp["ctrl_pick"]
        if _picked in all_ids and _picked != st.session_state.selected_id:
            st.session_state.selected_id = _picked
            st.query_params.clear()
            st.rerun()
        elif _picked in all_ids:
            # Already matches, just clear the param
            st.query_params.clear()

    # ── App Header ──────────────────────────────────────────────────────────
    st.markdown(
        f"""<div style="
            background:linear-gradient(135deg,#08111f 0%,#0f2f3a 58%,#164e63 100%);
            border:1px solid #245064;border-radius:10px;padding:12px 20px;
            display:flex;align-items:center;gap:18px;
            box-shadow:0 10px 30px rgba(0,0,0,0.18);margin-bottom:10px;
            flex-wrap:wrap;">
          <div style="flex-shrink:0;width:40px;height:40px;border-radius:50%;
                      background:linear-gradient(135deg,#14b8a6,#2563eb);
                      display:flex;align-items:center;justify-content:center;
                      font-size:16px;font-weight:800;color:white;">E</div>
          <div>
            <div style="font-size:10px;font-weight:700;color:#67e8f9;
                        text-transform:uppercase;letter-spacing:1px;">ECC-NIST Framework</div>
            <div style="font-size:20px;font-weight:800;color:#f8fafc;line-height:1.2;
                        font-family:'Inter',sans-serif;">Control Mapping Viewer</div>
            <div style="font-size:12px;color:#8aa3b8;margin-top:2px;">
              Active: <span style="color:#8bd3dd;font-weight:700;">{st.session_state.selected_id}</span>
            </div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── 3-column layout ──────────────────────────────────────────────────────
    col_left, col_center, col_right = st.columns([1.4, 4.0, 1.6])

    # ── LEFT: ECC Controls ──────────────────────────────────────────────────
    with col_left:
        search_term = st.text_input(
            "Search", placeholder="e.g. 2.1 or 3.3",
            key="ecc_search", label_visibility="collapsed",
        )
        filtered = (
            [c for c in all_ids if search_term.strip().lower() in c.lower()]
            if search_term.strip() else all_ids
        ) or all_ids

        cur = st.session_state.selected_id
        if cur not in filtered:
            cur = filtered[0]
            st.session_state.selected_id = cur

        # Build pill buttons — each one is a real anchor link with ?ctrl_pick=ID
        # No JS needed: clicking navigates, Streamlit reruns, query param handler at
        # top of app picks it up, updates session_state, clears param, reruns again.
        base_url = "?"
        pills_html = ""
        for cid in filtered:
            cls = "cpill active" if cid == cur else "cpill"
            href = "?" + urllib.parse.urlencode({"ctrl_pick": cid})
            pills_html += f'<a class="{cls}" href="{href}">{cid}</a>'

        n_shown = len(filtered)
        n_total = len(all_ids)

        grid_html = f"""
<div style="background:#0b1728;border:1px solid #1d2b3f;border-radius:10px;
            overflow:hidden;margin-top:4px;">
  <div style="font-size:10px;font-weight:800;color:#67e8f9;text-transform:uppercase;
              letter-spacing:.9px;padding:8px 10px 5px;border-bottom:1px solid #1d2b3f;">
    ECC Controls
    <span style="color:#475569;font-weight:400;font-size:9px;margin-left:6px;">
      {n_shown} of {n_total}
    </span>
  </div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:5px;
              padding:6px 8px 10px;max-height:400px;overflow-y:auto;
              scrollbar-width:thin;scrollbar-color:#28415c #0b1728;">
    {pills_html}
  </div>
</div>
<style>
.cpill{{
  background:#0a1628;border:1px solid #1d2b3f;border-radius:6px;
  color:#94a3b8;font-size:13px;font-weight:700;font-family:Inter,sans-serif;
  padding:7px 3px;text-align:center;cursor:pointer;
  transition:all .12s;white-space:normal;word-break:break-all;
  line-height:1.3;width:100%;display:flex;align-items:center;
  justify-content:center;min-height:34px;text-decoration:none;
}}
.cpill:hover{{background:#112338;border-color:#2d4a6a;color:#c8dce8;}}
.cpill.active{{
  background:linear-gradient(135deg,#0f766e,#2563eb);
  border-color:transparent;color:#fff;font-weight:800;
  box-shadow:0 0 8px rgba(20,184,166,.35);
}}
</style>
<script>
// Scroll active pill into view on page load
(function(){{
  const a = document.querySelector(".cpill.active");
  if (a) a.scrollIntoView({{block:"nearest", behavior:"smooth"}});
}})();
</script>
"""
        st.markdown(grid_html, unsafe_allow_html=True)
        selected_id = st.session_state.selected_id

    # ── RIGHT: Top-K + Workflow Steps (static label) + Export ───────────────
    with col_right:
        # Top-K card
        st.markdown(
            """<div class="topk-card">
              <div class="topk-title">Top-K</div>
              <div class="topk-sub">Mappings shown</div>
            </div>""",
            unsafe_allow_html=True,
        )
        top_k = st.select_slider(
            "Top-K",
            options=list(range(1, 6)),
            value=5,
            label_visibility="collapsed",
        )

        # "Scoring Steps" card — replaces "Pipeline", clearly labelled as static/pre-computed
        st.markdown(
            """<div class="workflow-card">
              <div class="workflow-title">Scoring Steps</div>
              <div class="workflow-sub">Pre-computed — not live</div>
            </div>""",
            unsafe_allow_html=True,
        )
        steps = [
            "Load ECC Control", "Load NIST Controls", "Extract Metadata",
            "Semantic Embeddings", "Ontology Scoring", "Confidence Match",
            "AI Explanation", "Return Top-K",
        ]
        rows_html = "".join(
            f'<div style="font-size:11px;color:#86efac;padding:2px 0">✓ {s}</div>'
            for s in steps
        )
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#0b1728,#103044);'
            f'border:1px solid #245064;border-radius:10px;padding:10px 12px;'
            f'margin-top:6px">{rows_html}</div>',
            unsafe_allow_html=True,
        )

        # ── Export button directly under the workflow steps ──────────────────
        st.markdown(
            """<div style="height:1px;background:linear-gradient(90deg,#1e293b,#4f46e5,#1e293b);
                           margin:10px 0 8px"></div>
               <div style="font-size:11px;font-weight:700;color:#e2e8f0;margin-bottom:6px;">
                 Export Report
               </div>""",
            unsafe_allow_html=True,
        )
        # We need the data prepared first; use a placeholder, fill after data is ready
        export_placeholder = st.empty()

    # ── Prepare data ─────────────────────────────────────────────────────────
    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    src_col  = find_col(list(df.columns), "Source Text")
    src_text = safe_value(row.get(src_col, "") if src_col else "")
    mappings = extract_mappings(row, df, top_k=top_k)

    # Fill export button now that data is ready
    pdf_bytes = generate_pdf(selected_id, src_text, mappings)
    with export_placeholder:
        if pdf_bytes:
            st.download_button(
                label="⬇ Download PDF Report",
                data=pdf_bytes,
                file_name=f"{selected_id}_mapping_report.pdf",
                mime="application/pdf",
            )
        else:
            st.warning("PDF export requires fpdf2 — install with: pip install fpdf2")

    # ── CENTER: Graph Viewer (ECC desc + details live inside the HTML panel) ──
    with col_center:
        viewer_html = create_viewer(str(selected_id), src_text, mappings)
        components.html(viewer_html, height=680, scrolling=True)

else:
    st.markdown(
        f"""<div style="background:#1e293b;border:1px solid #dc2626;border-radius:10px;
                        padding:24px;margin-top:30px;">
          <div style="font-size:16px;font-weight:700;color:#fca5a5;margin-bottom:8px;">
            Data file not found
          </div>
          <div style="color:#94a3b8;font-size:14px;">
            Make sure <code style="color:#818cf8">{DATA_FILE}</code> is in the same folder.
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
