import streamlit as st
import pandas as pd
from core.matchmaker import approve_linkage


def render_approvals(mentors_df: pd.DataFrame, partners_df: pd.DataFrame,
                     xai_chat_dialog_fn, query_xai_fn):
    st.markdown('<h3>Pending Approvals</h3>', unsafe_allow_html=True)

    if not st.session_state.processed_startups:
        st.info("No pitch decks processed yet.")
        return

    # keep xai open on rerun
    if st.session_state.xai_open and st.session_state.xai_open in st.session_state.processed_startups:
        xai_chat_dialog_fn(
            st.session_state.xai_open,
            st.session_state.processed_startups[st.session_state.xai_open],
            mentors_df,
            partners_df,
            query_xai_fn
        )

    for filename, analysis in list(st.session_state.processed_startups.items()):
        startup      = analysis.get("startup", {})
        startup_name = startup.get("name", "Unknown Startup")
        mentor       = analysis.get("mentor", {})
        partner      = analysis.get("partner", {})

        with st.expander(f'Startup Profile: {startup_name}', expanded=True):
            # dismiss btn
            _, dismiss_col = st.columns([20, 1])
            with dismiss_col:
                if st.button("", icon=":material/close:", key=f"dismiss_{filename}",
                             help="Dismiss this card", use_container_width=True):
                    del st.session_state.processed_startups[filename]
                    if filename in st.session_state.xai_chats:
                        del st.session_state.xai_chats[filename]
                    st.session_state.toast_msg  = f"'{startup_name}' dismissed."
                    st.session_state.toast_type = "success"
                    st.rerun()

            col_info, col_matches = st.columns([1, 2])

            with col_info:
                st.markdown('<p style="color: #8b949e; font-size: 0.85em; text-transform: uppercase; font-weight: 600;">Startup Profile</p>', unsafe_allow_html=True)
                st.markdown(f"**Industry:** {startup.get('industry', 'N/A')}")
                st.markdown(f"**Core Challenge:** {startup.get('challenges', 'N/A')}")

            with col_matches:
                st.markdown('<p style="color: #8b949e; font-size: 0.85em; text-transform: uppercase; font-weight: 600;">Recommended Linkages</p>', unsafe_allow_html=True)

                st.markdown(f'**<span class="material-symbols-outlined" style="font-size: 18px;">person</span> Mentor Match:** {mentor.get("name", "N/A")}', unsafe_allow_html=True)
                st.caption(f"{mentor.get('reason', '')}")

                if ((st.session_state.linkages_df["Target Startup"] == startup_name) &
                        (st.session_state.linkages_df["Matched Entity"] == mentor.get('name'))).any():
                    st.success("Mentor Match Approved")
                else:
                    if st.button("Approve Mentor", key=f"app_m_{filename}", type="primary"):
                        approve_linkage(startup_name, mentor.get('name'), "Mentor", mentor.get('reason'))
                        st.session_state.xai_open  = None
                        st.session_state.toast_msg  = "Mentor linkage approved!"
                        st.session_state.toast_type = "success"
                        st.rerun()

                st.markdown("---")

                st.markdown(f'**<span class="material-symbols-outlined" style="font-size: 18px;">handshake</span> Partner Match:** {partner.get("name", "N/A")}', unsafe_allow_html=True)
                st.caption(f"{partner.get('reason', '')}")

                if ((st.session_state.linkages_df["Target Startup"] == startup_name) &
                        (st.session_state.linkages_df["Matched Entity"] == partner.get('name'))).any():
                    st.success("Partner Match Approved")
                else:
                    if st.button("Approve Partner", key=f"app_p_{filename}", type="primary"):
                        approve_linkage(startup_name, partner.get('name'), "Partner", partner.get('reason'))
                        st.session_state.xai_open  = None
                        st.session_state.toast_msg  = "Partner linkage approved!"
                        st.session_state.toast_type = "success"
                        st.rerun()

            # open xai btn
            st.markdown("")
            if st.button(
                "Ask AI — Why these matches?",
                key=f"xai_btn_{filename}",
                icon=":material/psychology:",
                help="Open the Explainability Chat for this startup"
            ):
                st.session_state.xai_open = filename
                st.rerun()
