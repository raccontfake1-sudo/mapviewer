
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
            background:linear-gradient(135deg,#08111f 0%,#0f2f3a 58%,#164e63 100%);
            border:1px solid #245064;
            border-radius:10px;padding:12px 20px;
            display:flex;align-items:center;gap:18px;
            box-shadow:0 10px 30px rgba(0,0,0,0.18);
            margin-bottom:10px;
        ">
          <div style="flex-shrink:0;width:40px;height:40px;border-radius:50%;
                      background:linear-gradient(135deg,#14b8a6,#2563eb);
                      display:flex;align-items:center;justify-content:center;
                      font-size:16px;font-weight:800;color:white;">E</div>
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

    # ── Main viewer + right-side controls ───────────────────────────────
    col_v, col_p = st.columns([4.4, 1.65])

    with col_p:
        topk_col, pipe_col = st.columns([1, 1])
        with topk_col:
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
        with pipe_col:
            st.markdown(
                """<div class="pipeline-card">
                  <div class="pipeline-title">Pipeline</div>
                  <div class="pipeline-sub">Status</div>
                </div>""",
                unsafe_allow_html=True,
            )
        pipe_box = st.empty()
        steps = ["Load ECC Control","Load NIST Controls","Extract Metadata",
                 "Semantic Embeddings","Ontology Scoring","Confidence Match",
                 "AI Explanation","Return Top-K"]
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
                f'margin-top:8px">{rows_html}</div>',
                unsafe_allow_html=True,
            )
            time.sleep(0.12)

    mappings = extract_mappings(row, df, top_k=top_k)

    with col_v:
        viewer_html = create_viewer(str(selected_id), src_text, mappings)
        components.html(viewer_html, height=700, scrolling=True)

    # ── Export (only thing below) ──────────────────────────────────────
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
