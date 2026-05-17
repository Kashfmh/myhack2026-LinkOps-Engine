import pandas as pd
import streamlit as st


def render_sidebar(mentors_df: pd.DataFrame, partners_df: pd.DataFrame,
                   mentor_pool_dialog, partner_pool_dialog):
    with st.sidebar:
        st.markdown(
            '<div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">'
            '<span class="material-symbols-outlined" style="color:#1f6feb; font-size:28px;">hub</span>'
            '<span style="font-size:1.2rem; font-weight:700;">LinkOps Engine</span>'
            '</div>',
            unsafe_allow_html=True
        )
        st.caption("Ecosystem Matchmaking Dashboard · v2.4.0")
        st.divider()

        # stats
        st.markdown('<p style="color:#8b949e; font-size:0.78em; text-transform:uppercase; font-weight:600; margin-bottom:6px;">Session Overview</p>', unsafe_allow_html=True)

        files_queued    = len(st.session_state.get("file_manager", []))
        files_processed = len(st.session_state.get("processed_startups", {}))
        approved_count  = len(st.session_state.get("linkages_df", pd.DataFrame()))
        pending_count   = max(0, files_processed - sum(
            1 for fn in st.session_state.get("processed_startups", {})
            if not st.session_state.get("linkages_df", pd.DataFrame()).empty
            and fn in st.session_state.get("linkages_df", pd.DataFrame()).get("Target Startup", pd.Series()).values
        ))

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Files Queued", files_queued)
            st.metric("Approved", approved_count)
        with col_b:
            st.metric("Processed", files_processed)
            st.metric("Pending", files_processed - min(files_processed, approved_count // 2))

        st.divider()

        # db viewers
        st.markdown('<p style="color:#8b949e; font-size:0.78em; text-transform:uppercase; font-weight:600; margin-bottom:6px;">Ecosystem Pools</p>', unsafe_allow_html=True)
        if st.button("Browse Mentor Pool", use_container_width=True, icon=":material/person_search:"):
            st.session_state.xai_open = None  # close xai to avoid dialog overlap
            mentor_pool_dialog()
        if st.button("Browse Partner Pool", use_container_width=True, icon=":material/handshake:"):
            st.session_state.xai_open = None
            partner_pool_dialog()

        st.divider()

        # csv export
        if not st.session_state.get("linkages_df", pd.DataFrame()).empty:
            csv_data = st.session_state.linkages_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Export Ledger CSV",
                data=csv_data,
                file_name="linkops_ledger.csv",
                mime="text/csv",
                use_container_width=True,
                icon=":material/download:"
            )
        else:
            st.caption("No approved linkages to export yet.")
