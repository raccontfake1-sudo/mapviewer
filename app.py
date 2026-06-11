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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        
        /* Deep Blue Main App Background (No Green) */
        .stApp { background: #030815; color: #e2e8f0; }

        /* Left Sidebar Compliance Blue Tones */
        section[data-testid="stSidebar"] {
            background: #040c1e;
            border-right: 1px solid #14284b;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding: 0.8rem 0.75rem 1rem;
        }
        section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
        
        .side-head {
            border: 1px solid #14284b;
            border-radius: 8px;
            padding: 9px 10px;
            margin-bottom: 8px;
            background: linear-gradient(135deg,#071224 0%,#0c2246 100%);
        }
        .side-kicker {
            color: #60a5fa !important;
            font-size: 9px;
            font-weight: 800;
            letter-spacing: 0.8px;
            text-transform: uppercase;
        }
        .side-title {
            color: #f8fafc !important;
            font-size: 15px;
            font-weight: 800;
            line-height: 1.2;
            margin-top: 2px;
        }
        .side-count {
            color: #8da2bb !important;
            font-size: 11px;
            margin: -2px 0 8px;
        }
        section[data-testid="stSidebar"] input[type="text"] {
            background: #061124 !important; border: 1px solid #193560 !important;
            border-radius: 8px !important; color: #f1f5f9 !important;
            font-size: 13px !important; padding: 7px 10px !important;
        }
        section[data-testid="stSidebar"] input[type="text"]::placeholder { color: #475569 !important; }
        section[data-testid="stSidebar"] .stTextInput,
        section[data-testid="stSidebar"] .stRadio {
            margin-bottom: 0.35rem !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            max-height: calc(100vh - 190px);
            overflow-y: auto;
            gap: 0 !important;
            padding-right: 4px;
            scrollbar-width: thin;
            scrollbar-color: #193560 #040c1e;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"]::-webkit-scrollbar { width: 4px; }
        section[data-testid="stSidebar"] div[role="radiogroup"]::-webkit-scrollbar-track { background: #040c1e; }
        section[data-testid="stSidebar"] div[role="radiogroup"]::-webkit-scrollbar-thumb {
            background: #193560;
            border-radius: 4px;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: 4px 7px !important;
            margin: 1px 0 !important;
            border-radius: 6px !important;
            transition: background 0.15s ease !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: #0c1c38 !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label div,
        section[data-testid="stSidebar"] div[role="radiogroup"] label p,
        section[data-testid="stSidebar"] div[role="radiogroup"] label span {
            font-size: 12px !important;
            font-weight: 600 !important;
            line-height: 1.25 !important;
            text-transform: none !important;
            letter-spacing: 0 !important;
            color: #d1dfed !important;
        }

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] label p {
            font-size: 10px !important; font-weight: 600 !important;
            text-transform: uppercase !important; letter-spacing: 0.8px !important;
            color: #728da6 !important; margin-bottom: 4px !important;
        }

        .main .block-container,
        .block-container,
        div[data-testid="stAppViewBlockContainer"] {
            padding: 0.65rem 1rem 1.25rem !important;
            margin-top: 0 !important;
            max-width: 1540px !important;
        }
        .main .block-container > div:first-child { margin-top: 0 !important; }

        .stDownloadButton button {
            background: linear-gradient(135deg,#1d4ed8,#2563eb) !important;
            color: white !important; border: none !important;
            border-radius: 8px !important; font-weight: 600 !important;
            font-size: 14px !important; padding: 10px 22px !important;
        }
        .stDownloadButton button:hover {
            background: linear-gradient(135deg,#1e40af,#1d4ed8) !important;
        }

        #MainMenu { visibility: hidden; }
        footer    { visibility: hidden; }
        header    { visibility: hidden; }

        /* Cards Styled with Compliance Blue (Replacing Teals) */
        .topk-card {
            background: linear-gradient(135deg,#061124,#0e264e);
            border: 1px solid #1e3a8a;
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
            color: #93c5fd !important;
            margin-top: 3px;
        }
        .pipeline-card {
            background: linear-gradient(135deg,#061124,#0d254b);
            border: 1px solid #1e40af;
            border-radius: 8px;
            padding: 10px 12px 6px;
            min-height: 54px;
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
            color: #93c5fd !important;
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
            background: #3b82f6 !important;
            border-color: #ffffff !important;
            box-shadow: 0 0 0 2px rgba(59,130,246,0.18) !important;
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
    if score >= 0.85:   return "#00c853", "#00e676", "High Match",   "🟢"
    elif score >= 0.70: return "#ffab00", "#ffd600", "Medium Match", "🟡"
    else:               return "#d50000", "#ff1744", "Low Match",    "🔴"


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
        pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(37, 99, 235)
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
            pdf.set_font("Helvetica","B",10); pdf.set_text_color(3b,82,f6); pdf.cell(0,6,label,ln=True)
            pdf.set_font("Helvetica","",10); pdf.set_text_color(55,65,81)
            pdf.multi_cell(0,5.5,str(value).encode("latin-1","replace").decode("latin-1")); pdf.ln(2)
        pdf.set_font("Helvetica","B",10); pdf.set_text_color(37,99,235); pdf.cell(0,6,"Scores",ln=True)
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
    # Graph geometry
    W, H     = 560, 420
    cx, cy   = 280, 210
    BR, GR   = 38, 32      # Core radii
    ORBIT    = 145          # orbit radius

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

        # connector line
        dx, dy = x - cx, y - cy
        dist = math.sqrt(dx*dx + dy*dy)
        sx = cx + (BR / dist) * dx;  sy = cy + (BR / dist) * dy
        ex = x  - (GR / dist) * dx;  ey = y  - (GR / dist) * dy
        svg_lines += f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{col}" stroke-width="1.5" stroke-dasharray="5,3" opacity="0.55"/>\n'

        # rank label
        svg_nums += f'<text x="{x:.1f}" y="{y - GR - 8:.1f}" text-anchor="middle" fill="{col}" font-size="10" font-weight="700" font-family="Inter,sans-serif">#{rank}</text>\n'

        # node group  ← onclick stores rank in JS
        svg_nodes += f"""<g class="mnode" onclick="return selectNode({rank}, event)" data-rank="{rank}" data-color="{col}">
  <circle cx="{x:.1f}" cy="{y:.1f}" r="{GR+6}" fill="{col}" opacity="0.15" class="gring"/>
  <circle cx="{x:.1f}" cy="{y:.1f}" r="{GR}" fill="{col}"/>
  <text x="{x:.1f}" y="{y-7:.1f}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="13" font-weight="800" font-family="Inter,sans-serif">{code}</text>
  <text x="{x:.1f}" y="{y+9:.1f}" text-anchor="middle" dominant-baseline="middle" fill="rgba(255,255,255,0.9)" font-size="13" font-weight="700" font-family="Inter,sans-serif">{html.escape(pct)}</text>
</g>\n"""

    mdata_json   = json.dumps(mapping_data,  ensure_ascii=False)
    srows_json   = json.dumps(summary_rows,  ensure_ascii=False)
    src_json     = json.dumps(source_text,   ensure_ascii=False)
    src_id_json  = json.dumps(str(selected_id), ensure_ascii=False)
    n_mappings   = len(mappings)

    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{font-family:'Inter',sans-serif;background:#030815;color:#e2e8f0;min-height:100%;overflow:auto}}

/* ── Outer Shell Two-Column Layout ── */
.shell{{
  display:flex;width:100%;height:680px;min-height:680px;overflow:hidden;
  border:1px solid #14284b;border-radius:12px;
  box-shadow:0 18px 42px rgba(0,0,0,0.22);
}}

/* ── LEFT: Graph (Pure Compliance Blue - No Green) ── */
.graph-col{{
  flex:0 0 58%;
  display:flex;flex-direction:column;
  background:radial-gradient(circle at 50% 40%,rgba(37,99,235,0.15),transparent 34%),
             linear-gradient(160deg,#030a16 0%,#0a1f3d 56%,#0e316a 100%);
  border-right:1px solid #14284b;
  position:relative;overflow:hidden;
}}
.graph-header{{
  display:flex;align-items:center;gap:10px;
  padding:14px 18px 10px;
  border-bottom:1px solid #14284b;
  flex-shrink:0;
}}
.graph-badge{{
  background:linear-gradient(135deg,#1e40af,#3b82f6);
  color:white;font-size:9px;font-weight:700;letter-spacing:1px;
  text-transform:uppercase;padding:3px 10px;border-radius:20px;
}}
.graph-title{{font-size:13px;font-weight:700;color:#e2e8f0}}
.graph-subtitle{{font-size:11px;color:#8da2bb;margin-top:1px}}
.svg-wrap{{flex:1;display:flex;align-items:center;justify-content:center;padding:8px 0 0}}
.svg-wrap svg{{width:min(100%,560px);height:auto;overflow:visible}}
.legend{{
  display:flex;gap:14px;padding:10px 18px 14px;
  border-top:1px solid #14284b;flex-shrink:0;
}}
.leg{{display:flex;align-items:center;gap:5px;font-size:10px;font-weight:600;color:#8da2bb}}
.legdot{{width:9px;height:9px;border-radius:50%;flex-shrink:0}}

/* ── RIGHT: Table + Details Scroll Panel ── */
.right-col{{
  flex:1;min-width:320px;display:flex;flex-direction:column;
  background:#050f24;overflow:hidden;
}}

/* Summary levels */
.tbl-section{{flex-shrink:0;border-bottom:1px solid #14284b}}
.tbl-header{{padding:12px 16px 8px;background:#050f24}}
.tbl-title{{font-size:12px;font-weight:700;color:#e2e8f0;display:flex;align-items:center;gap:6px}}
.tbl-sub{{font-size:10px;color:#728da6;margin-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{
  background:linear-gradient(135deg,#1e40af,#3b82f6);
  color:white;padding:8px 12px;text
