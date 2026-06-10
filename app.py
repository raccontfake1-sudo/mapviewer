import math
import json
import html

def create_svg_viewer(selected_id, source_text, mappings, hide_circles=False):
    width = 620
    height = 600
    center_x = 310
    center_y = 220
    blue_radius = 48
    green_radius = 42
    graph_radius = 158

    # Prepare mapping data for JS
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

        fill_color, glow_color, text_color, badge_color = score_to_node_colors(item["final"])
        score_pct = format_percent(item["final"])

        # Save for JS interaction
        mapping_data[node_id] = {
            "rank": str(rank),
            "mapping": item["mapping"],
            "final": format_decimal(item["final"]),
            "final_percent": format_percent(item["final"]),
            "embed": format_decimal(item["embedding"]),
            "embed_percent": format_percent(item["embedding"]),
            "ontology": format_decimal(item["ontology"]),
            "ontology_percent": format_percent(item["ontology"]),
            "commonality": item["commonality"],
            "justification": item["justification"],
            "differences": item["differences"],
            "fill_color": fill_color,
            "glow_color": glow_color,
        }

        dx = x - center_x
        dy = y - center_y
        distance = math.sqrt(dx*dx + dy*dy)

        start_x = center_x + (blue_radius / distance) * dx
        start_y = center_y + (blue_radius / distance) * dy
        end_x = x - (green_radius / distance) * dx
        end_y = y - (green_radius / distance) * dy

        # Draw lines
        svg_lines += f'''
            <line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}"
                  stroke="{fill_color}" stroke-width="1.8"
                  stroke-dasharray="5,3" opacity="0.6"/>
        '''

        # Draw nodes if not hidden
        if not hide_circles:
            svg_nodes += f'''
                <g class="mapping-node" onclick="updatePanel('{node_id}')" data-fill="{fill_color}">
                    <circle cx="{x}" cy="{y}" r="{green_radius}" fill="{fill_color}" filter="drop-shadow(0 3px 8px {glow_color})"/>
                    <text x="{x}" y="{y - 8}" text-anchor="middle" dominant-baseline="middle" class="node-code">{html.escape(item["short_code"])}</text>
                    <text x="{x}" y="{y + 10}" text-anchor="middle" dominant-baseline="middle" class="node-score">{html.escape(score_pct)}</text>
                </g>
            '''

        # Number labels
        svg_numbers += f'''
            <text x="{x}" y="{y - green_radius - 9}" class="number-label" fill="{fill_color}">{rank}</text>
        '''

    # Serialize data for JavaScript
    mapping_data_json = json.dumps(mapping_data)
    selected_id_json = json.dumps(str(selected_id))
    source_text_json = json.dumps(source_text)

    # Compose full HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<style>
  body {{
    font-family: 'Inter', Arial, sans-serif;
    margin: 0; padding: 0;
    background: #f8faff;
  }}
  .mapping-node:hover .glow-ring {{
    opacity: 0.38 !important;
  }}
  .number-label {{
    font-size: 10px; font-weight: 700; font-family: 'Inter', Arial, sans-serif;
  }}
  /* Toggle button styles */
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
</style>
</head>
<body>
<div style="width:100%; height:100%; overflow:auto;">
<svg viewBox="0 0 {width} {height}" style="width:100%; height:100%;">
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
      </stop>
    </defs>
    <!-- Center node -->
    <g onclick="showEccPanel()">
      <circle cx="{center_x}" cy="{center_y}" r="{blue_radius + 10}" fill="url(#centerGlow)" opacity="0.22"/>
      <circle cx="{center_x}" cy="{center_y}" r="{blue_radius}" fill="url(#centerGrad)" filter="drop-shadow(0 4px 14px rgba(99,102,241,0.55))"/>
      <text x="{center_x}" y="{center_y - 8}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="13" font-weight="800">ECC</text>
      <text x="{center_x}" y="{center_y + 8}" text-anchor="middle" dominant-baseline="middle" fill="rgba(255,255,255,0.85)" font-size="10" font-weight="700">{html.escape(str(selected_id))}</text>
      <text x="{center_x}" y="{center_y + 22}" text-anchor="middle" dominant-baseline="middle" fill="rgba(255,255,255,0.55)" font-size="8" font-weight="500">click</text>
    </g>
</svg>
</div>
<button id="toggleBtn" onclick="toggleCircles()">Hide Circles</button>
<script>
  const mappingData = {mapping_data_json};
  const selectedId = {selected_id_json};
  const sourceText = {source_text_json};

  function showEccPanel() {{
    document.getElementById('detailPanel').innerHTML = `
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
        <div style="font-size:24px;">🔵</div>
        <div>
          <div style="font-weight:700; font-size:15px;">ECC Control</div>
          <div style="font-size:11px; color:#94a3b8;">Source control description</div>
        </div>
      </div>
      <div style="margin-top:8px; font-weight:600;">Control ID: ${html.escape(selected_id)}</div>
      <div style="margin-top:8px; line-height:1.5;">${html.escape(source_text)}</div>
      <div style="margin-top:12px; font-weight:600; font-size:13px; color:#4f46e5;">Click a node for details</div>
    `;
  }}

  function updatePanel(nodeId) {{
    const item = mappingData[nodeId];
    if (!item) return;
    let finalScore = parseFloat(item.final);
    let matchIcon = finalScore >= 0.85 ? "🟢" : finalScore >= 0.70 ? "🟡" : "🔴";
    let matchLabel = finalScore >= 0.85 ? "High Match" : finalScore >= 0.70 ? "Medium Match" : "Low Match";

    document.getElementById('detailPanel').innerHTML = `
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
        <div style="font-size:24px;">${matchIcon}</div>
        <div>
          <div style="font-weight:700; font-size:15px;">Mapping #${item.rank} Details</div>
          <div style="font-size:11px; color:#94a3b8;">${html.escape(item.mapping)}</div>
        </div>
      </div>
      <div style="margin-top:8px; font-weight:600;">Scores & Analysis</div>
      <div style="display:flex; gap:10px; margin-top:4px;">
        <div style="background:#6366f1; color:#fff; padding:8px; border-radius:8px; flex:1;">
          <div style="font-size:11px;">Final Score</div>
          <div style="font-weight:700; font-size:14px;">${html.escape(item.final_percent)}</div>
        </div>
        <div style="background:#0891b2; color:#fff; padding:8px; border-radius:8px; flex:1;">
          <div style="font-size:11px;">Embedding</div>
          <div style="font-weight:700; font-size:14px;">${html.escape(item.embed)}</div>
        </div>
        <div style="background:#059669; color:#fff; padding:8px; border-radius:8px; flex:1;">
          <div style="font-size:11px;">Ontology</div>
          <div style="font-weight:700; font-size:14px;">${html.escape(item.ontology)}</div>
        </div>
      </div>
      <div style="margin-top:8px; font-size:12px;">Confidence: <b>${matchLabel}</b></div>
      <div style="margin-top:8px; font-weight:600;">NIST Control</div>
      <div style="margin-bottom:8px;">${html.escape(item.mapping)}</div>
      <div style="margin-top:8px; font-weight:600;">Commonality</div>
      <div>${html.escape(item.commonality)}</div>
      <div style="margin-top:8px; font-weight:600;">Justification</div>
      <div>${html.escape(item.justification)}</div>
      <div style="margin-top:8px; font-weight:600;">Differences</div>
      <div>${html.escape(item.differences)}</div>
    `;
  }}

  function toggleCircles() {{
    const nodes = document.querySelectorAll('.mapping-node');
    const btn = document.getElementById('toggleBtn');
    if (nodes.length === 0) return;
    const displayState = nodes[0].style.display;
    const newState = displayState === 'none' ? 'block' : 'none';
    for (const node of nodes) {{
      node.style.display = newState;
    }}
    btn.innerText = newState === 'none' ? 'Show Circles' : 'Hide Circles';
  }}

  // Initialize number labels color based on selection
  document.addEventListener('DOMContentLoaded', () => {{
    document.querySelectorAll('.number-label').forEach(lbl => {{
      const nodeId = lbl.getAttribute('data-node-id');
      lbl.setAttribute('fill', nodeId === {json.dumps(str(selected_id))} ? 'white' : '{score_to_node_colors(0)[0]}');
    }});
  }});
</script>
</body>
</html>
"""
    return html
