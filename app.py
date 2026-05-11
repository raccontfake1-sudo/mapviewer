    # عنوان الصفحة
    st.markdown(f'<div class="main-title">Control Mapping Viewer</div>', unsafe_allow_html=True)
    st.write(f"Viewing: **{selected_id}**")

    # 1. عرض الرسم البياني
    graph_html = create_styled_graph(str(selected_id), str(row_data["Source Text"]), all_mappings)
    components.html(graph_html, height=620)

    # 2. عرض قسم AI Explanations (البيانات كاملة)
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.markdown('<div class="main-title" style="font-size: 1.8em;">AI Explanations</div>', unsafe_allow_html=True)
    
    for idx, m in enumerate(all_mappings):
        # استخدام Expander لعرض البيانات بشكل منظم كما في الصورة
        with st.expander(f"#{idx+1} - {m['mapping']}", expanded=(idx == 0)):
            st.markdown(f"""
            <div class="explanation-box">
                <span class="exp-header">#{idx+1} - {m['mapping']}</span>
                
                <span class="exp-label">Commonality:</span>
                <p class="exp-content">{m['commonality']}</p>
                
                <span class="exp-label">Justification:</span>
                <p class="exp-content">{m['justification']}</p>
                
                <span class="exp-label">Differences:</span>
                <p class="exp-content">{m['differences']}</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("لم يتم العثور على ملف البيانات CSV. تأكد من وجوده في نفس المجلد.")
