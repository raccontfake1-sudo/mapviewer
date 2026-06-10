import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os, math, json, html, re

st.set_page_config(page_title="ECC-NIST Control Mapping Viewer", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
  background: linear-gradient(180deg, #0b1220 0%, #0f172a 60%, #111827 100%);
  color: #e5e7eb;
}

section[data-testid="stSidebar"] {
  background: #0b1220;
  border-right: 1px solid #1f2937;
}
section[data-testid="stSidebar"] * { color: #e5e7eb !important; }

/* Slider tick labels (1 and 5) white */
.stSlider [data-baseweb="slider"] div,
.stSlider [data-baseweb="slider"] span,
.stSlider .StyledThumbValue,
.stSlider [data-testid="stTickBar"] *,
.stSlider div { color: #ffffff !important; }

/* Compact ECC header */
.ecc-header {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; padding: 14px 18px; border-radius: 14px;
  background: linear-gradient(135deg, #1e293b, #0f172a);
  border: 1px solid #1f2937; margin-bottom: 14px;
}
.ecc-header .eyebrow {
  font-size: 11px; letter-spacing: .14em; text-transform: uppercase;
  color: #93c5fd; font-weight: 600;
}
.ecc-header .title { font-size: 20px; font-weight: 700; color: #f8fafc; margin-top: 2px; }
.ecc-header .sub { font-size: 13px; color: #94a3b8; margin-top: 2px; }
.ecc-header .pill {
  background: #1e3a8a; color: #dbeafe; padding: 6px 12px;
  border-radius: 999px; font-size: 12px; font-weight: 600;
}

.section-card {
  background: #111827; border: 1px solid #1f2937;
  border-radius: 14px; padding: 16px; margin-bottom: 14px;
}
.section-title {
  font-size: 13px; text-transform: uppercase; letter-spacing: .12em;
  color: #94a3b8; font-weight: 600; margin-bottom: 10px;
}

.row {
  display:flex; align-items:center; justify-content:space-between;
  padding: 10px 12px; border-radius: 10px; cursor: pointer;
  border: 1px solid transparent; transition: all .15s;
}
.row:hover { background:#1f2937; border-color:#374151; }
.row .code { color:#f1f5f9; font-weight:600; font-size:13px; }
.row .desc { color:#94a3b8; font-size:12px; margin-top:2px; }
.badge {
  background:#1e40af; color:#dbeafe; padding:4px 10px;
  border-radius: 999px; font-size: 12px; font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Data ----------------
CSV_PATH = "final_with_explanations_COMPLETE.csv"

st.sidebar.markdown("### Data")
uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded is not None:
    df = pd.read_csv(uploaded)
elif os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    st.info(f"Place **{CSV_PATH}** next to this script, or upload it from the sidebar.")
    st.stop()

# Normalize columns we expect
expected = ["ecc_code", "ecc_description", "nist_code", "nist_description", "score", "explanation"]
for c in expected:
    if c not in df.columns:
        st.error(f"CSV missing column: {c}")
        st.stop()

df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)

# ---------------- Sidebar controls ----------------
st.sidebar.markdown("### Filters")
q = st.sidebar.text_input("Search ECC code or text", "")
top_k = st.sidebar.slider("Top-K mappings", 1, 5, 3)

ecc_options = sorted(df["ecc_code"].dropna().unique().tolist())
if q:
    ql = q.lower()
    ecc_options = [c for c in ecc_options if ql in c.lower() or
                   ql in str(df[df.ecc_code == c]["ecc_description"].iloc[0]).lower()]

if not ecc_options:
    st.warning("No ECC controls match your search.")
    st.stop()

selected_ecc = st.sidebar.radio("ECC Control", ecc_options, index=0)

# ---------------- ECC header (compact) ----------------
ecc_row = df[df.ecc_code == selected_ecc].iloc[0]
ecc_desc = str(ecc_row["ecc_description"])

st.markdown(f"""
<div class="ecc-header">
  <div>
    <div class="eyebrow">ECC Control</div>
    <div class="title">{html.escape(selected_ecc)}</div>
    <div class="sub">{html.escape(ecc_desc[:160])}{'…' if len(ecc_desc)>160 else ''}</div>
  </div>
  <div class="pill">Top {top_k} NIST mappings</div>
</div>
""", unsafe_allow_html=True)

# ---------------- Top-K results ----------------
subset = (df[df.ecc_code == selected_ecc]
          .sort_values("score", ascending=False)
          .head(top_k)
          .reset_index(drop=True))

col_graph, col_side = st.columns([4, 1])

# ---------------- SVG viewer ----------------
def create_svg_viewer(ecc_code, ecc_desc, mappings):
    W, H = 900, 520
    cx, cy = W//2, H//2
    nodes_js = []
    for i, r in mappings.iterrows():
        angle = (2 * math.pi * i) / max(len(mappings), 1) - math.pi/2
        radius = 190
        nx = cx + radius * math.cos(angle)
        ny = cy + radius * math.sin(angle)
        nodes_js.append({
            "x": nx, "y": ny,
            "code": str(r["nist_code"]),
            "desc": str(r["nist_description"]),
            "score": float(r["score"]),
            "explanation": str(r.get("explanation", ""))
        })

    nodes_json = json.dumps(nodes_js)
    ecc_payload = json.dumps({"code": ecc_code, "desc": ecc_desc})

    html_doc = f"""
<!doctype html><html><head><meta charset="utf-8">
<style>
  html,body{{margin:0;padding:0;background:transparent;font-family:Inter,sans-serif;}}
  .wrap{{display:flex;gap:14px;align-items:flex-start;}}
  svg{{background:#0b1220;border:1px solid #1f2937;border-radius:14px;display:block;}}
  .node{{cursor:pointer;transition:transform .15s;}}
  .node:hover{{transform:scale(1.05);transform-origin:center;}}
  #detail{{flex:0 0 280px;background:#111827;border:1px solid #1f2937;
    border-radius:14px;padding:14px;color:#e5e7eb;font-size:13px;min-height:200px;}}
  #detail h3{{margin:0 0 6px;font-size:14px;color:#f8fafc;}}
  #detail .badge{{display:inline-block;background:#1e40af;color:#dbeafe;
    padding:3px 9px;border-radius:999px;font-size:11px;font-weight:700;margin-bottom:8px;}}
  #detail .label{{color:#94a3b8;font-size:11px;text-transform:uppercase;
    letter-spacing:.1em;margin-top:10px;margin-bottom:4px;}}
  #detail .body{{color:#cbd5e1;line-height:1.45;}}
</style></head><body>
<div class="wrap">
  <svg id="g" viewBox="0 0 {W} {H}" width="100%" preserveAspectRatio="xMidYMid meet"></svg>
  <div id="detail"><h3>Click a circle</h3>
    <div class="body">Select a NIST node or the central ECC to see details.</div></div>
</div>
<script>
const W={W},H={H},cx={cx},cy={cy};
const nodes={nodes_json};
const ecc={ecc_payload};
const svg=document.getElementById('g');
const detail=document.getElementById('detail');

function el(tag,attrs,children){{
  const n=document.createElementNS('http://www.w3.org/2000/svg',tag);
  for(const k in attrs) n.setAttribute(k,attrs[k]);
  if(children) for(const c of children) n.appendChild(c);
  return n;
}}
function text(x,y,t,opts){{
  const n=el('text',Object.assign({{x,y,'text-anchor':'middle','dominant-baseline':'middle',
    fill:'#e5e7eb','font-size':12,'font-family':'Inter'}},opts||{{}}));
  n.textContent=t; return n;
}}

// Draw lines first
nodes.forEach(n=>{{
  svg.appendChild(el('line',{{x1:cx,y1:cy,x2:n.x,y2:n.y,
    stroke:'#334155','stroke-width':1.5,'stroke-dasharray':'4 4'}}));
}});

// Center ECC node
const center=el('g',{{class:'node'}});
center.appendChild(el('circle',{{cx,cy,r:60,fill:'#1e3a8a',stroke:'#3b82f6','stroke-width':2}}));
center.appendChild(text(cx,cy-6,ecc.code,{{'font-weight':700,'font-size':14,fill:'#dbeafe'}}));
center.appendChild(text(cx,cy+12,'ECC',{{'font-size':10,fill:'#93c5fd'}}));
center.addEventListener('click',e=>{{e.stopPropagation();showECC();}});
svg.appendChild(center);

// NIST nodes
nodes.forEach((n,i)=>{{
  const g=el('g',{{class:'node'}});
  g.appendChild(el('circle',{{cx:n.x,cy:n.y,r:42,fill:'#065f46',stroke:'#10b981','stroke-width':2}}));
  g.appendChild(text(n.x,n.y-4,n.code.length>10?n.code.slice(0,10)+'…':n.code,
    {{'font-weight':700,'font-size':11,fill:'#d1fae5'}}));
  g.appendChild(text(n.x,n.y+12,'★ '+n.score.toFixed(2),{{'font-size':10,fill:'#a7f3d0'}}));
  g.addEventListener('click',e=>{{e.stopPropagation();showNode(i);}});
  svg.appendChild(g);
}});

function esc(s){{return (s||'').toString()
  .replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');}}

function showECC(){{
  detail.innerHTML=`<h3>${{esc(ecc.code)}}</h3>
    <span class="badge">ECC SOURCE</span>
    <div class="label">Description</div>
    <div class="body">${{esc(ecc.desc)}}</div>`;
}}
function showNode(i){{
  const n=nodes[i];
  detail.innerHTML=`<h3>${{esc(n.code)}}</h3>
    <span class="badge">SCORE ${{n.score.toFixed(2)}}</span>
    <div class="label">NIST Description</div>
    <div class="body">${{esc(n.desc)}}</div>
    <div class="label">Why it maps</div>
    <div class="body">${{esc(n.explanation)}}</div>`;
}}
showECC();
</script></body></html>
"""
    return html_doc

with col_graph:
    components.html(create_svg_viewer(selected_ecc, ecc_desc, subset),
                    height=560, scrolling=True)

with col_side:
    st.markdown('<div class="section-card"><div class="section-title">Mappings</div>',
                unsafe_allow_html=True)
    for _, r in subset.iterrows():
        st.markdown(f"""
          <div class="row">
            <div>
              <div class="code">{html.escape(str(r['nist_code']))}</div>
              <div class="desc">{html.escape(str(r['nist_description'])[:60])}…</div>
            </div>
            <div class="badge">{r['score']:.2f}</div>
          </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Table ----------------
with st.expander("Full mapping table"):
    st.dataframe(subset, use_container_width=True)
