import base64
import time
import streamlit as st
import pandas as pd
from config import XAI_MAX_MSGS, XAI_COOLDOWN_SEC, XAI_MAX_CHARS


@st.dialog("Mentor Pool", width="large")
def mentor_pool_dialog(mentors_df: pd.DataFrame):
    st.caption(f"{len(mentors_df)} mentors in the ecosystem database")
    st.dataframe(
        mentors_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Name":      st.column_config.TextColumn("Name",      width="medium"),
            "Industry":  st.column_config.TextColumn("Industry",  width="small"),
            "Expertise": st.column_config.TextColumn("Expertise", width="large"),
        }
    )


@st.dialog("Partner Pool", width="large")
def partner_pool_dialog(partners_df: pd.DataFrame):
    st.caption(f"{len(partners_df)} partners in the ecosystem database")
    st.dataframe(
        partners_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Name":       st.column_config.TextColumn("Name",       width="medium"),
            "Focus Area": st.column_config.TextColumn("Focus Area", width="large"),
        }
    )


@st.dialog("Document Preview", width="large")
def preview_dialog(file_dict: dict):
    if file_dict['type'] == "application/pdf":
        b64 = base64.b64encode(file_dict['bytes']).decode()
        pdf_html = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800" style="border:none;"></iframe>'
        st.markdown(pdf_html, unsafe_allow_html=True)
    else:
        st.image(file_dict['bytes'], use_container_width=True)


@st.dialog("Explainability Chat", width="large")
def xai_chat_dialog(filename: str, analysis: dict, mentors_df: pd.DataFrame,
                    partners_df: pd.DataFrame, query_xai_fn):
    startup      = analysis.get("startup", {})
    startup_name = startup.get("name", "Unknown Startup")
    mentor       = analysis.get("mentor", {})
    partner      = analysis.get("partner", {})

    if filename not in st.session_state.xai_chats:
        st.session_state.xai_chats[filename] = [{
            "role": "assistant",
            "content": (
                f"I matched **{startup_name}** with **{mentor.get('name')}** as mentor and "
                f"**{partner.get('name')}** as partner. "
                f"Ask me anything about these recommendations \u2014 why I picked them, "
                f"why I didn't pick others, or anything else about this startup's profile."
            )
        }]
    if filename not in st.session_state.xai_rate:
        st.session_state.xai_rate[filename] = {"count": 0, "last_ts": 0.0}

    rate           = st.session_state.xai_rate[filename]
    history        = st.session_state.xai_chats[filename]
    user_msg_count = sum(1 for m in history if m["role"] == "user")
    needs_ai       = history and history[-1]["role"] == "user"

    # chat container
    with st.container(height=420, border=False):
        for msg in history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if needs_ai:
            with st.chat_message("assistant"):
                ai_reply = st.write_stream(
                    query_xai_fn(analysis, history[:-1], history[-1]["content"],
                                 mentors_df, partners_df)
                )
            history.append({"role": "assistant", "content": ai_reply})
            st.rerun()

    # chat input needs to be at bottom
    if needs_ai:
        pass
    elif user_msg_count >= XAI_MAX_MSGS:
        st.warning(f"Message limit reached ({XAI_MAX_MSGS} messages per session).")
    else:
        user_q = st.chat_input("Ask the AI about these matches...", key=f"xai_dlg_{filename}")
        if user_q:
            now = time.time()
            if len(user_q) > XAI_MAX_CHARS:
                st.session_state.toast_msg  = f"Message too long. Limit is {XAI_MAX_CHARS} characters."
                st.session_state.toast_type = "error"
            elif (now - rate["last_ts"]) < XAI_COOLDOWN_SEC:
                st.session_state.toast_msg  = f"Please wait {XAI_COOLDOWN_SEC}s between messages."
                st.session_state.toast_type = "error"
            else:
                rate["count"]  += 1
                rate["last_ts"] = now
                history.append({"role": "user", "content": user_q})
                st.rerun()
