import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from ui.styles    import inject_styles, show_toast
from ui.dialogs   import mentor_pool_dialog, partner_pool_dialog, xai_chat_dialog
from ui.sidebar   import render_sidebar
from ui.file_manager import render_file_manager
from ui.approvals import render_approvals
from ui.ledger    import render_ledger
from core.matchmaker import execute_match_protocol, query_xai

# setup & icons
st.set_page_config(
    page_title="LinkOps Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_styles()

# load live ecosystem databases
mentors_df  = pd.read_csv("data/mentors.csv")
partners_df = pd.read_csv("data/partners.csv")

# pool dialog wrappers (bind dataframes so sidebar can call them without args)
def open_mentor_pool():
    mentor_pool_dialog(mentors_df)

def open_partner_pool():
    partner_pool_dialog(partners_df)

# sidebar
render_sidebar(mentors_df, partners_df, open_mentor_pool, open_partner_pool)

# init state variables
if "linkages_df" not in st.session_state:
    st.session_state.linkages_df = pd.DataFrame(
        columns=["Target Startup", "Matched Entity", "Type", "Status", "Match Reason"]
    )
if "processed_startups" not in st.session_state:
    st.session_state.processed_startups = {}
if "file_manager" not in st.session_state:
    st.session_state.file_manager = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 1
if "xai_chats" not in st.session_state:
    st.session_state.xai_chats = {}
if "xai_open" not in st.session_state:
    st.session_state.xai_open = None
if "xai_rate" not in st.session_state:
    st.session_state.xai_rate = {}
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "pending_delete" not in st.session_state:
    st.session_state.pending_delete = None
if "toast_msg" not in st.session_state:
    st.session_state.toast_msg = None
if "toast_type" not in st.session_state:
    st.session_state.toast_type = "success"

# custom toast cuz st.toast is ugly
if st.session_state.toast_msg:
    show_toast(st.session_state.toast_msg, st.session_state.toast_type)
    st.session_state.toast_msg = None

# main sections
render_file_manager(execute_match_protocol, mentors_df, partners_df)

st.divider()

render_approvals(mentors_df, partners_df, xai_chat_dialog, query_xai)

st.divider()

render_ledger()

# hidden js triggers
components.html("""
<script>
const parent = window.parent.document;
const buttons = parent.querySelectorAll("button");
buttons.forEach(btn => {
    if(btn.innerText === "RESET_PENDING_DELETE") {
        btn.parentElement.parentElement.style.display = 'none';
    }
});
</script>
""", height=0)

if st.button("RESET_PENDING_DELETE"):
    st.session_state.pending_delete = None
    st.rerun()