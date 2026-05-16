import streamlit as st
import pandas as pd
from google import genai
import json
import base64
import streamlit.components.v1 as components
import time
import random
import concurrent.futures

# setup & icons
st.set_page_config(
    page_title="LinkOps Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# styling hacks for ui
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@400,0&display=swap" rel="stylesheet">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Geist', sans-serif; }
    .material-symbols-outlined { vertical-align: middle; padding-bottom: 3px; }
    div.stButton > button[kind="primary"] { border-radius: 0.5rem; font-weight: 600; border: 1px solid #388bfd; }
    [data-testid="stExpander"] { border: 1px solid #30363d !important; border-radius: 0.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
    [data-testid="stFileUploader"] { border: 2px dashed #30363d !important; border-radius: 0.5rem; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* fix padding */
    .block-container {
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important;
    }
    
    [data-testid="stSidebarHeader"] {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
    }

    /* keep sidebar toggle visible */
    [data-testid="stSidebarHeader"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        opacity: 1 !important;
        visibility: visible !important;
        transition: none !important;
    }

    /* align buttons */
    [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4) button,
    [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(5) button {
        width: 46px !important;
        min-width: 46px !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    /* warning state for delete btns */
    [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(5) button[data-pending="true"],
    button[kind="secondary"][aria-label="Confirm deletion"] {
        color: #f59e0b !important;
        border-color: #f59e0b !important;
        background-color: rgba(245, 158, 11, 0.08) !important;
    }

    /* custom dropzone ui */
    [data-testid="stFileUploaderDropzone"] {
        background-color: transparent !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 3.5rem !important;
    }
    [data-testid="stFileUploaderDropzone"] > div,
    [data-testid="stFileUploaderDropzone"] > button,
    [data-testid="stFileUploaderDropzone"] > span {
        display: none !important;
    }
    [data-testid="stFileUploaderDropzone"]::before {
        content: "cloud_upload";
        font-family: 'Material Symbols Outlined';
        font-size: 28px;
        color: #c9d1d9;
        background-color: #21262d;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 16px;
    }
    [data-testid="stFileUploaderDropzone"]::after {
        content: "Drop Startup Pitch Decks\\A PDF or Image files supported for bulk processing.";
        white-space: pre-wrap;
        text-align: center;
        font-size: 16px;
        font-weight: 600;
        color: #e6edf3;
        line-height: 1.6;
    }
    [data-testid="stFileUploaderDropzone"]:hover::before {
        background-color: #30363d;
    }

    /* center modals */
    [data-testid="stModal"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* skeleton - match dark theme so the flash isn't jarring */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #0d1117;
    }
    [data-testid="stSkeleton"] {
        background: linear-gradient(
            90deg,
            #161b22 0px,
            #21262d 40px,
            #161b22 80px
        ) !important;
        background-size: 600px 100% !important;
        animation: sk-shimmer 1.6s infinite linear !important;
        border-radius: 4px !important;
    }
    @keyframes sk-shimmer {
        0%   { background-position: -600px 0; }
        100% { background-position:  600px 0; }
    }
    /* sidebar skeleton bg */
    [data-testid="stSidebar"] {
        background-color: #161b22;
    }
    /* mobile: sidebar hidden so suppress its skeleton */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] [data-testid="stSkeleton"] {
            display: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# mock dbs for the demo
mentors_df = pd.DataFrame([
    {"Name": "Dr. Sarah Chen", "Expertise": "Fintech scaling & regulatory compliance", "Industry": "Fintech"},
    {"Name": "Ahmad Razali", "Expertise": "AgriTech supply chains & enterprise sales", "Industry": "AgriTech"},
    {"Name": "Maria Gomez", "Expertise": "HealthTech data privacy & hospital integrations", "Industry": "HealthTech"},
    {"Name": "David Lee", "Expertise": "EdTech user growth & product strategy", "Industry": "EdTech"}
])

partners_df = pd.DataFrame([
    {"Name": "Global Bank", "Focus Area": "Fintech partnerships & regulatory sandboxes"},
    {"Name": "AgriCorp", "Focus Area": "AgriTech pilots & distribution networks"},
    {"Name": "National Health", "Focus Area": "HealthTech pilots & legacy integrations"}
])

# modals for browsing pools
@st.dialog("Mentor Pool", width="large")
def mentor_pool_dialog():
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
def partner_pool_dialog():
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

# sidebar stuff
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
def show_toast(message, type="success"):
    color = "#10b981" if type == "success" else "#ef4444"
    bg = "#10b9810d" if type == "success" else "#ef44440d"
    icon = "check_circle" if type == "success" else "error"
    
    css = f"""
    <style>
    @keyframes toastFadeInOut {{
        0% {{ opacity: 0; transform: translate(-50%, -20px); }}
        10% {{ opacity: 1; transform: translate(-50%, 0); }}
        80% {{ opacity: 1; transform: translate(-50%, 0); }}
        100% {{ opacity: 0; transform: translate(-50%, -20px); visibility: hidden; }}
    }}
    .custom-toast-msg {{
        position: fixed;
        top: 24px;
        left: 50%;
        background-color: {bg};
        border: 1px solid {color};
        color: {color};
        padding: 12px 24px;
        border-radius: 8px;
        z-index: 999999;
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        animation: toastFadeInOut 3s forwards;
        pointer-events: none;
    }}
    </style>
    <div class="custom-toast-msg">
        <span class="material-symbols-outlined">{icon}</span>
        {message}
    </div>
    """
    st.markdown(css, unsafe_allow_html=True)

# file previewer
@st.dialog("Document Preview", width="large")
def preview_dialog(file_dict):
    if file_dict['type'] == "application/pdf":
        b64 = base64.b64encode(file_dict['bytes']).decode()
        pdf_html = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800" style="border:none;"></iframe>'
        st.markdown(pdf_html, unsafe_allow_html=True)
    else:
        st.image(file_dict['bytes'], use_container_width=True)

class DummyFile:
    def __init__(self, f_dict):
        self.name = f_dict['name']
        self.type = f_dict['type']
        self.bytes = f_dict['bytes']
    def getvalue(self):
        return self.bytes

# xai chat modal
@st.dialog("Explainability Chat", width="large")
def xai_chat_dialog(filename, analysis):
    startup = analysis.get("startup", {})
    startup_name = startup.get("name", "Unknown Startup")
    mentor  = analysis.get("mentor", {})
    partner = analysis.get("partner", {})

    MAX_MSGS     = 20
    COOLDOWN_SEC = 3
    MAX_CHARS    = 500

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

    needs_ai = history and history[-1]["role"] == "user"

    # chat container
    with st.container(height=420, border=False):
        for msg in history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if needs_ai:
            with st.chat_message("assistant"):
                ai_reply = st.write_stream(
                    query_xai(analysis, history[:-1], history[-1]["content"])
                )
            history.append({"role": "assistant", "content": ai_reply})
            st.rerun()

    # chat input needs to be at bottom
    if needs_ai:
        pass
    elif user_msg_count >= MAX_MSGS:
        st.warning(f"Message limit reached ({MAX_MSGS} messages per session).")
    else:
        user_q = st.chat_input("Ask the AI about these matches...", key=f"xai_dlg_{filename}")
        if user_q:
            now = time.time()
            if len(user_q) > MAX_CHARS:
                st.session_state.toast_msg  = f"Message too long. Limit is {MAX_CHARS} characters."
                st.session_state.toast_type = "error"
            elif (now - rate["last_ts"]) < COOLDOWN_SEC:
                st.session_state.toast_msg  = f"Please wait {COOLDOWN_SEC}s between messages."
                st.session_state.toast_type = "error"
            else:
                rate["count"]  += 1
                rate["last_ts"] = now
                history.append({"role": "user", "content": user_q})
                st.rerun()

# ai logic & constraints
SAFETY_SYSTEM_INSTRUCTION = (
    "You are an enterprise decision support AI for Cradle Fund Malaysia. "
    "STRICT SAFETY RULE: Refuse to process any content related to Malaysian 3R issues "
    "(Race, Religion, Royalty) or LGBTQ+ topics. "
)

def execute_match_protocol(uploaded_file) -> dict | None:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        st.error("ERROR: GEMINI_API_KEY not found in Streamlit secrets.")
        return None

    prompt = f"""
You are an enterprise ecosystem-matching engine.
Analyze the provided Target Entity (Startup) Pitch Deck.
1. Extract the Startup's Name, Industry, and Core Challenge.
2. Identify the single best Mentor match from the available list.
3. Identify the single best Partner match from the available list.
4. For each match, provide a strict 2-sentence logical justification.

### Available Mentors
{mentors_df.to_string(index=False)}

### Available Partners
{partners_df.to_string(index=False)}

### Output Format
Return EXACTLY valid JSON with this structure:
{{
  "startup": {{
    "name": "<Startup Name>",
    "industry": "<Startup Industry>",
    "challenges": "<Startup Core Challenge>"
  }},
  "mentor": {{
    "name": "<Mentor Name>",
    "reason": "<2-sentence justification>"
  }},
  "partner": {{
    "name": "<Partner Name>",
    "reason": "<2-sentence justification>"
  }}
}}
"""
    try:
        client = genai.Client(api_key=api_key)
        
        file_part = genai.types.Part.from_bytes(
            data=uploaded_file.getvalue(),
            mime_type=uploaded_file.type
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[file_part, prompt],
            config=genai.types.GenerateContentConfig(
                system_instruction=SAFETY_SYSTEM_INSTRUCTION,
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Protocol Error for {uploaded_file.name}: {str(e)}")
        return None

def approve_linkage(startup_name: str, entity_name: str, entity_type: str, reason: str):
    if not ((st.session_state.linkages_df["Target Startup"] == startup_name) & 
            (st.session_state.linkages_df["Matched Entity"] == entity_name)).any():
        
        new_row = pd.DataFrame([{
            "Target Startup": startup_name,
            "Matched Entity": entity_name,
            "Type": entity_type,
            "Status": "Approved",
            "Match Reason": reason
        }])
        st.session_state.linkages_df = pd.concat([st.session_state.linkages_df, new_row], ignore_index=True)

def query_xai(analysis: dict, chat_history: list, user_question: str):
    # stream xai chunks back to ui
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        yield "Error: API key not configured."
        return

    startup = analysis.get("startup", {})
    mentor  = analysis.get("mentor", {})
    partner = analysis.get("partner", {})

    system_context = f"""You are a focused Explainable AI assistant inside the LinkOps Engine — a startup ecosystem matchmaking platform.

YOUR ROLE: Help the human admin understand and interrogate the AI matchmaking decisions for this specific startup.

SCOPE RULES:
- You MAY answer any question related to: this startup's profile, the mentor/partner selected, why any other person or entity (even if they are not in the database) was or was not chosen, comparisons between candidates, or the matchmaking logic in general.
- If someone asks about a name that does not appear in the database, explain clearly that the person is not in the available pool and cannot be considered.
- You MUST refuse ONLY questions that have absolutely no connection to matchmaking, this startup, or this platform. Examples of things to refuse: writing code, telling jokes, general trivia, political opinions, tasks unrelated to this tool.
- When refusing, respond with exactly: "I'm only able to discuss matters related to these match recommendations."
- Do NOT change your recommendations. Only explain them.
- Be concise, direct, and factual.

--- STARTUP PROFILE ---
Name: {startup.get('name', 'N/A')}
Industry: {startup.get('industry', 'N/A')}
Core Challenge: {startup.get('challenges', 'N/A')}

--- YOUR DECISIONS ---
Mentor Matched: {mentor.get('name', 'N/A')}
Mentor Reason: {mentor.get('reason', 'N/A')}

Partner Matched: {partner.get('name', 'N/A')}
Partner Reason: {partner.get('reason', 'N/A')}

--- ALL AVAILABLE MENTORS (the only options in the system) ---
{mentors_df.to_string(index=False)}

--- ALL AVAILABLE PARTNERS (the only options in the system) ---
{partners_df.to_string(index=False)}

If a user asks about someone not in the above lists, confirm they are not in the database and explain why the chosen candidates are more suitable."""

    contents = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(genai.types.Content(role=role, parts=[genai.types.Part(text=msg["content"])]))
    contents.append(genai.types.Content(role="user", parts=[genai.types.Part(text=user_question)]))

    try:
        client = genai.Client(api_key=api_key)
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=contents,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_context,
                temperature=0.3,
            ),
        ):
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"XAI Error: {str(e)}"

# main ui headers
if st.session_state.toast_msg:
    show_toast(st.session_state.toast_msg, st.session_state.toast_type)
    st.session_state.toast_msg = None

st.markdown('<h1 style="font-size: 2.5rem; margin-bottom: 0;">LinkOps Engine</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #8b949e; font-size: 1.1rem; margin-top: 0;">Automated Linkage Engine for Program Administrators</p>', unsafe_allow_html=True)
st.write("")

# file uploader
MAX_FILES = 5
MAX_FILE_SIZE_MB = 10

uploaded_new = st.file_uploader(
    "Drop Startup Pitch Decks (PDF/Images) here for bulk processing", 
    type=["pdf", "png", "jpg", "jpeg"], 
    accept_multiple_files=True,
    label_visibility="collapsed",
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded_new:
    added = False
    for f in uploaded_new:
        if len(st.session_state.file_manager) >= MAX_FILES:
            st.session_state.toast_msg = f"Maximum {MAX_FILES} files allowed."
            st.session_state.toast_type = "error"
            break
            
        if f.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.session_state.toast_msg = f"'{f.name}' exceeds the {MAX_FILE_SIZE_MB}MB limit."
            st.session_state.toast_type = "error"
            continue
            
        # prevent dupes
        if not any(existing['name'] == f.name for existing in st.session_state.file_manager):
            st.session_state.file_manager.append({
                "name": f.name,
                "type": f.type,
                "size": f.size,
                "bytes": f.getvalue()
            })
            added = True
            
    if added:
        st.session_state.uploader_key += 1
        st.session_state.toast_msg = "Files uploaded successfully!"
        st.session_state.toast_type = "success"
        st.rerun()

# file list ui
if st.session_state.file_manager:
    st.markdown('<div style="margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 600; color: #8b949e; text-transform: uppercase; font-size: 0.85em;">Ready for Processing:</div>', unsafe_allow_html=True)
    
    for idx, f in enumerate(st.session_state.file_manager):
        is_analysed = f['name'] in st.session_state.processed_startups
        with st.container(border=True):
            col_icon, col_name, col_status, col_size, col_eye, col_x = st.columns([0.5, 6, 2, 2, 0.7, 0.7], vertical_alignment="center")
            
            with col_icon:
                icon = "picture_as_pdf" if f['type'] == "application/pdf" else "image"
                st.markdown(f'<span class="material-symbols-outlined" style="color: #8b949e;">{icon}</span>', unsafe_allow_html=True)
                
            with col_name:
                st.markdown(f"<span style='color:#e6edf3; font-weight: 500;'>{f['name']}</span>", unsafe_allow_html=True)

            with col_status:
                if is_analysed:
                    st.markdown(
                        '<span style="background:rgba(16,185,129,0.1); color:#10b981; border:1px solid #10b981; '
                        'border-radius:999px; padding:2px 10px; font-size:11px; font-weight:600; '
                        'display:inline-flex; align-items:center; gap:4px;">'
                        '<span class="material-symbols-outlined" style="font-size:13px;">check_circle</span>'
                        'Analysed</span>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<span style="background:rgba(245,158,11,0.1); color:#f59e0b; border:1px solid #f59e0b; '
                        'border-radius:999px; padding:2px 10px; font-size:11px; font-weight:600; '
                        'display:inline-flex; align-items:center; gap:4px;">'
                        '<span class="material-symbols-outlined" style="font-size:13px;">schedule</span>'
                        'Pending</span>',
                        unsafe_allow_html=True
                    )
                
            with col_size:
                st.markdown(f"<span style='color:#8b949e; font-size:12px;'>{f['size'] / 1024 / 1024:.2f} MB</span>", unsafe_allow_html=True)
                
            with col_eye:
                if st.button("", icon=":material/visibility:", key=f"eye_{idx}_{f['name']}", help="Preview file"):
                    preview_dialog(f)
                    
            with col_x:
                is_pending = st.session_state.pending_delete == f['name']
                btn_icon = ":material/warning:" if is_pending else ":material/close:"
                btn_help = "Confirm deletion" if is_pending else "Remove file"
                
                if st.button("", icon=btn_icon, key=f"del_{idx}_{f['name']}", type="secondary", help=btn_help):
                    if is_pending:
                        st.session_state.file_manager.pop(idx)
                        st.session_state.pending_delete = None
                        st.session_state.toast_msg = "File deleted."
                        st.session_state.toast_type = "success"
                        st.rerun()
                    else:
                        st.session_state.pending_delete = f['name']
                        st.rerun()

        # 3s auto revert hack for delete btn
        if st.session_state.pending_delete == f['name']:
            components.html("""
            <script>
            setTimeout(() => {
                const parent = window.parent.document;
                const buttons = parent.querySelectorAll("button");
                buttons.forEach(btn => {
                    if(btn.innerText === "RESET_PENDING_DELETE") {
                        btn.click();
                    }
                });
            }, 3000);
            </script>
            """, height=0)

    st.write("")

    if st.session_state.is_processing:
        # processing state logic
        files_to_process = [f for f in st.session_state.file_manager
                            if f['name'] not in st.session_state.processed_startups]
        total = len(files_to_process)
        progress_bar = st.progress(0)
        status_text  = st.empty()

        for i, f in enumerate(files_to_process):
            file_start  = int((i / total) * 100)
            file_target = int(((i + 0.85) / total) * 100)

            status_text.markdown(
                f"Analysing **{f['name']}** &nbsp;({i+1}/{total})",
                unsafe_allow_html=True
            )

            # bg thread for api so ui doesnt freeze completely
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(execute_match_protocol, DummyFile(f))

                current = file_start
                while not future.done() and current < file_target:
                    remaining  = file_target - current
                    increment  = random.randint(1, max(1, remaining // 4))
                    current    = min(current + increment, file_target)
                    progress_bar.progress(current)
                    time.sleep(random.uniform(0.18, 0.45))

                analysis = future.result()

            if analysis:
                st.session_state.processed_startups[f['name']] = analysis

            # snap progress
            progress_bar.progress(int(((i + 1) / total) * 100))

        # check fails
        actually_processed = sum(
            1 for f in files_to_process if f['name'] in st.session_state.processed_startups
        )
        failed = total - actually_processed

        st.session_state.is_processing = False
        time.sleep(0.4)

        if actually_processed == 0:
            progress_bar.progress(0)
            status_text.markdown("Processing failed. No decks were analysed.")
            st.session_state.toast_msg  = f"Failed to process all {total} file(s). Check your API quota."
            st.session_state.toast_type = "error"
        elif failed > 0:
            status_text.markdown(f"{actually_processed} of {total} processed. {failed} failed.")
            st.session_state.toast_msg  = f"{actually_processed} of {total} deck(s) processed. {failed} failed — check API quota."
            st.session_state.toast_type = "error"
        else:
            progress_bar.progress(100)
            status_text.markdown("All decks processed successfully!")
            st.session_state.toast_msg  = f"{total} deck(s) processed successfully!"
            st.session_state.toast_type = "success"

        time.sleep(0.6)
        st.rerun()

    else:
        # idle state
        new_files = [f for f in st.session_state.file_manager
                     if f['name'] not in st.session_state.processed_startups]
        all_done   = len(new_files) == 0
        btn_label  = (
            "All Files Already Analysed"
            if all_done
            else f"Analyse {len(new_files)} New File{'s' if len(new_files) != 1 else ''}"
        )
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            if st.button(btn_label, type="primary", use_container_width=True,
                         disabled=all_done,
                         help="All uploaded files have already been analysed." if all_done else None):
                st.session_state.is_processing = True
                st.rerun()

st.divider()

# hitl approvals
st.markdown('<h3>Pending Approvals</h3>', unsafe_allow_html=True)

if not st.session_state.processed_startups:
    st.info("No pitch decks processed yet.")
else:
    # keep xai open on rerun
    if st.session_state.xai_open and st.session_state.xai_open in st.session_state.processed_startups:
        xai_chat_dialog(st.session_state.xai_open, st.session_state.processed_startups[st.session_state.xai_open])

    for filename, analysis in list(st.session_state.processed_startups.items()):
        startup = analysis.get("startup", {})
        startup_name = startup.get("name", "Unknown Startup")
        mentor = analysis.get("mentor", {})
        partner = analysis.get("partner", {})
        
        expander_title = f'Startup Profile: {startup_name}'
        with st.expander(expander_title, expanded=True):
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

st.divider()

# history ledger
st.markdown('<h3>Approved Ecosystem Linkages</h3>', unsafe_allow_html=True)

if st.session_state.linkages_df.empty:
    st.info("No approved linkages yet.")
else:
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