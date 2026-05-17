import streamlit as st


def render_ledger():
    st.markdown('<h3>Approved Ecosystem Linkages</h3>', unsafe_allow_html=True)

    if st.session_state.linkages_df.empty:
        st.info("No approved linkages yet.")
        return

    df = st.session_state.linkages_df

    # rows
    rows_html = ""
    for _, row in df.iterrows():
        rows_html += (
            f"<tr>"
            f"<td style='white-space:nowrap;'>{row['Target Startup']}</td>"
            f"<td style='white-space:nowrap;'>{row['Matched Entity']}</td>"
            f"<td style='white-space:nowrap; width:60px;'>{row['Type']}</td>"
            f"<td style='white-space:nowrap; width:90px;'><span style='background:rgba(16,185,129,0.12);color:#10b981;"
            f"border:1px solid #10b981;border-radius:999px;padding:2px 10px;"
            f"font-size:11px;font-weight:600;white-space:nowrap;display:inline-block;'>{row['Status']}</span></td>"
            f"<td style='color:#c9d1d9;font-size:0.88em;line-height:1.6;width:50%;'>{row['Match Reason']}</td>"
            f"</tr>"
        )

    table_html = f"""
    <style>
    .linkage-table {{
        width: 100%; border-collapse: collapse;
        font-family: inherit; font-size: 0.9rem; color: #e6edf3;
    }}
    .linkage-table th {{
        text-align: left; padding: 10px 14px;
        background: #161b22; color: #8b949e;
        font-size: 0.75em; text-transform: uppercase;
        font-weight: 600; border-bottom: 1px solid #30363d;
    }}
    .linkage-table td {{
        padding: 10px 14px; vertical-align: top;
        border-bottom: 1px solid #21262d; word-break: break-word;
    }}
    .linkage-table tr:last-child td {{ border-bottom: none; }}
    .linkage-table tr:hover td {{ background: #1c2128; }}
    </style>
    <table class="linkage-table">
      <thead>
        <tr>
          <th>Target Startup</th><th>Matched Entity</th>
          <th>Type</th><th>Status</th><th>Match Reason</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    st.write("")

    csv_export = st.session_state.linkages_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Export to CSV",
        data=csv_export,
        file_name='cradle_ecosystem_ledger.csv',
        mime='text/csv'
    )
