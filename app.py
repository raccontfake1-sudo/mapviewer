import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import html
import os

st.set_page_config(page_title="Control Mapping Viewer", layout="wide")

def get_mapping_columns(i):
    suffix = "" if i == 1 else f" {i}"
    return {
        "mapping": f"NIST mapping{suffix}",
        "text": f"Text{suffix}",
        "final": f"Final Score{suffix}",
        "commonality": f"Commonality{suffix}",
        "justification": f"Justification{suffix}",
        "differences": f"Differences{suffix}"
    }

def extract_mappings(row, df, top_k=10):
    results = []

    for i in range(1, 11):
        cols = get_mapping_columns(i)

        if cols["mapping"] not in df.columns or pd.isna(row.get(cols["mapping"])):
            continue

        try:
            val = str(row.get(cols["final"], 0)).replace("%", "")
            score = float(val) / 100.0 if float(val) > 1.0 else float(val)
        except:
            score = 0.0

        commonality_val = row.get(cols["commonality"], "")
        justification_val = row.get(cols["justification"], "")
        differences_val = row.get(cols["differences"], "")

        if pd.isna(differences_val) or differences_val == "":
            differences_val = "The controls differ in implementation focus and specific requirements."

        results.append({
            "mapping": str(row.get(cols["mapping"], "")),
            "text": str(row.get(cols["text"], "")),
            "final": score,
            "commonality": str(commonality_val) if not pd.isna(commonality_val) else "N/A",
            "justification": str(justification_val) if not pd.isna(justification_val) else "N/A",
            "differences": str(differences_val)
        })

    return sorted(results, key=lambda x: x["final"], reverse=True)[:top_k]

def create_graph(selected_id, source_text, mappings):
    net = Network(height="650px", width="100%", bgcolor="#ffffff")

    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -100,
          "springLength": 200
        },
        "solver": "forceAtlas2Based",
        "stabilization": {
          "iterations": 1000
        }
      },
      "nodes": {
        "font": {
          "size": 18,
          "face": "arial"
        },
        "borderWidth": 2
      },
      "edges": {
        "font": {
          "size": 16,
          "align": "middle",
          "color": "#1476d4"
        },
        "color": "#d3dbe3"
      }
    }
    """)

    # الدائرة الزرقاء الرئيسية
   # الدائرة الزرقاء الرئيسية
    net.add_node(
  selected_id,
   label=str(selected_id),
   title=html.escape(source_text),
   color="#1687d9",
   size=220,
   shape="circle",
   font={"color": "white", "size": 40}
)

       # دوائر الـ mappings
    for idx, item in enumerate(mappings):

        edge_width = 3

        net.add_node(
            item["mapping"],
            label=item["mapping"],
            title=html.escape(item["text"]),
            color="#328a36",
            size=32,
            shape="circle",
            font={"color": "white"}
        )

        net.add_edge(
            selected_id,
            item["mapping"],
            label=f"{idx + 1}",
            width=edge_width
        ) 
  
          # الدائرة الزرقاء الرئيسية
    net.add_node(
        selected_id,
        label=str(selected_id),
        title=html.escape(source_text),
        color="#1687d9",
        size=220,
        shape="circle",
        font={"color": "white", "size": 40}
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return open(tmp.name, "r", encoding="utf-8").read()

DATA_FILE = "final_ontology_refined_mappings_with_explanations.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]

    st.sidebar.title("Controls List")

    control_ids = sorted(
        df["ECC id control"].astype(str).unique(),
        key=lambda x: int("".join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else 0
    )

    selected_id = st.sidebar.radio(
        "Select Control ID:",
        control_ids
    )

    st.title("Control Mapping Viewer")

    row = df[df["ECC id control"].astype(str) == str(selected_id)].iloc[0]
    mappings = extract_mappings(row, df)

    graph_html = create_graph(
        str(selected_id),
        str(row["Source Text"]),
        mappings
    )

    components.html(graph_html, height=680)

    st.markdown("## AI Explanations")

    if mappings:
        for idx, m in enumerate(mappings):
            with st.expander(f"{idx + 1} - {m['mapping']}"):
                st.markdown(f"**Commonality:** {m['commonality']}")
                st.markdown(f"**Justification:** {m['justification']}")
                st.markdown(f"**Differences:** {m['differences']}")
    else:
        st.info("No mappings found for this control.")

else:
    st.error("Data file not found. Please ensure the CSV is in the same directory.")

المشكلة مو من size 😭
المشكلة إن PyVis أحيانًا يثبّت حجم العقد حسب الـ physics.

أضيفي هذا السطر داخل الدائرة الزرقاء:

physics=False,

خليها كذا بالكامل:

net.add_node(
    selected_id,
    label=str(selected_id),
    title=html.escape(source_text),
    color="#1687d9",
    size=220,
    shape="circle",
    physics=False,
    font={"color": "white", "size": 40}
)

وبرضه احذفي النسخة الثانية هذي بالكامل:

# الدائرة الزرقاء الرئيسية
net.add_node(
    selected_id,
    label=str(selected_id),
    title=html.escape(source_text),
    color="#1687d9",
    size=220,
    shape="circle",
    font={"color": "white", "size": 40}
)

لأنها مكررة بدون physics=False.

بعدها سوّي:

streamlit run app.py

أو إذا على GitHub/Streamlit Cloud اضغطي:

Restart app
ثم Refresh

وبيطلع الفرق مباشرة 👍

File "/mount/src/mapviewer/app.py", line 122
           net.add_node(
          ^
IndentationError: unexpected indent
انت شايف الارقام من 1الي 10 ؟يبيها بالاترتيب 

بدلي هذا السطر:

"color": "#000000",

بهذا:

"color": "#003b8e",

أو إذا تبين أزرق أغمق وأوضح أكثر:

"color": "#001f5c",

بيطلع رقم الترتيب أزرق غامق وواضح 🔥

وين ذا

داخل net.set_options 👌

دوري هذا الجزء:

"edges": {
  "font": {
    "size": 16,
    "align": "middle",
    "color": "#1476d4"
  },

وغيريه إلى:

"edges": {
  "font": {
    "size": 35,
    "align": "middle",
    "color": "#001f5c",
    "strokeWidth": 5,
    "strokeColor": "#ffffff"
  },

هذا يغير:

لون أرقام الترتيب إلى أزرق غامق
ويكبرها
ويخليها أوضح 🔥
File "/mount/src/mapviewer/app.py", line 212, in <module>
    graph_html = create_graph(
        str(selected_id),
        str(row["Source Text"]),
        mappings
    )
File "/mount/src/mapviewer/app.py", line 59, in create_graph
      net.set_options("""
      ~~~~~~~~~~~~~~~^^^^
      {
      ^
    ...<19 lines>...
      }
      ^
      """)
      ^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/pyvis/network.py", line 1006, in set_options
    self.options = self.options.set(options)
                   ~~~~~~~~~~~~~~~~^^^^^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/pyvis/options.py", line 224, in set
    options = json.loads(options)
File "/usr/local/lib/python3.14/json/__init__.py", line 352, in loads
    return _default_decoder.decode(s)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^
File "/usr/local/lib/python3.14/json/decoder.py", line 345, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.14/json/decoder.py", line 361, in raw_decode
    obj, end = self.scan_once(s, idx)
               ~~~~~~~~~~~~~~^^^^^^^^

الخطأ لأن JSON داخل set_options صار فيه فاصلة أو تنسيق غلط بعد التعديل 😭

استبدلي جزء "edges" كامل بهذا بالضبط:

"edges": {
  "font": {
    "size": 35,
    "align": "middle",
    "color": "#001f5c",
    "strokeWidth": 5,
    "strokeColor": "#ffffff"
  },
  "color": "#d3dbe3"
}

وخليه داخل:

net.set_options("""
{
 ...
}
""")

المشكلة غالبًا إن "color": "#d3dbe3" كانت بمكان غلط أو ناقصة فاصلة ,.
