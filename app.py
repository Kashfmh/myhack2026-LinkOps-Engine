import streamlit as st
import pandas as pd
from google import genai
import json

# 1. PAGE CONFIG & MATERIAL ICONS
st.set_page_config(
    page_title="LinkOps Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Material Symbols & Structural CSS (Colors handled by config.toml)
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
    
    /* NEW: Shave off top padding in main page */
    .block-container {
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important;
    }
    
    /* NEW: Shave off top padding in sidebar */
    [data-testid="stSidebarHeader"] {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
    }

    /* Sidebar Toggle / Hamburger Fixes */
    /* 1. Prevent the button from hiding when not hovering */
    [data-testid="stSidebarHeader"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        opacity: 1 !important;
        visibility: visible !important;
        transition: none !important;
    }

    /* 2. Hide the default Streamlit chevron SVGs */
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="collapsedControl"] svg {
        display: none !important;
        opacity: 0 !important;
    }

    /* 3. Inject the Hamburger Icon directly into the buttons */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        position: relative !important;
    }
    [data-testid="stSidebarCollapseButton"]::after,
    [data-testid="collapsedControl"]::after {
        content: "\\e5d2" !important;
        font-family: 'Material Symbols Outlined' !important;
        font-size: 24px !important;
        color: #8b949e !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        pointer-events: none !important; /* Prevents icon from blocking clicks */
    }

    /* Custom File Uploader layout */
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
</style>
""", unsafe_allow_html=True)

# 2. THE SIDEBAR (Dark Mode Optimized)
with st.sidebar:
    st.markdown('### <span class="material-symbols-outlined" style="color: #1f6feb;">hub</span> Admin Console', unsafe_allow_html=True)
    st.caption("v2.4.0-stable")
    st.button("New Linkage", type="primary", use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Custom Navigation Links
    st.markdown('<div style="color: #c9d1d9; font-weight: 500; padding: 8px 0;"><span class="material-symbols-outlined" style="color: #8b949e; margin-right: 8px;">dashboard</span> Overview</div>', unsafe_allow_html=True)
    st.markdown('<div style="color: #8b949e; padding: 8px 0;"><span class="material-symbols-outlined" style="margin-right: 8px;">upload_file</span> Upload Center</div>', unsafe_allow_html=True)
    st.markdown('<div style="color: #8b949e; padding: 8px 0;"><span class="material-symbols-outlined" style="margin-right: 8px;">device_hub</span> Network Graph</div>', unsafe_allow_html=True)
    st.markdown('<div style="color: #8b949e; padding: 8px 0;"><span class="material-symbols-outlined" style="margin-right: 8px;">settings</span> Settings</div>', unsafe_allow_html=True)
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.divider()
    st.markdown('<div style="color: #8b949e; padding: 4px 0; font-size: 0.85em;"><span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">help</span> Support</div>', unsafe_allow_html=True)
    st.markdown('<div style="color: #8b949e; padding: 4px 0; font-size: 0.85em;"><span class="material-symbols-outlined" style="font-size: 16px; margin-right: 4px;">description</span> Documentation</div>', unsafe_allow_html=True)

# 3. MOCK DATABASES
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

# 4. SESSION STATE INITIALIZATION
if "linkages_df" not in st.session_state:
    st.session_state.linkages_df = pd.DataFrame(
        columns=["Target Startup", "Matched Entity", "Type", "Status", "Match Reason"]
    )

if "processed_startups" not in st.session_state:
    st.session_state.processed_startups = {}

# 5. SAFETY & AI LOGIC
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

# 6. MAIN UI HEADER
st.markdown('<h1 style="font-size: 2.5rem; margin-bottom: 0;">Ecosystem Graph AI</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #8b949e; font-size: 1.1rem; margin-top: 0;">Automated Linkage Engine for Program Administrators</p>', unsafe_allow_html=True)
st.write("")

# Bulk File Uploader
uploaded_files = st.file_uploader(
    "Drop Startup Pitch Decks (PDF/Images) here for bulk processing", 
    type=["pdf", "png", "jpg", "jpeg"], 
    accept_multiple_files=True,
    label_visibility="collapsed"
)
if uploaded_files:
        if st.button("Process Uploaded Decks", type="primary"):
            with st.spinner("Extracting and matching..."):
                for file in uploaded_files:
                    if file.name not in st.session_state.processed_startups:
                        analysis = execute_match_protocol(file)
                        if analysis:
                            st.session_state.processed_startups[file.name] = analysis

st.divider()

# 7. HUMAN-IN-THE-LOOP DASHBOARD
st.markdown('<h3>Pending Approvals</h3>', unsafe_allow_html=True)

if not st.session_state.processed_startups:
    st.info("No pitch decks processed yet.")
else:
    for filename, analysis in st.session_state.processed_startups.items():
        startup = analysis.get("startup", {})
        startup_name = startup.get("name", "Unknown Startup")
        
        expander_title = f'🏢 Startup Profile: {startup_name}'
        with st.expander(expander_title, expanded=True):
            col_info, col_matches = st.columns([1, 2])
            
            with col_info:
                st.markdown('<p style="color: #8b949e; font-size: 0.85em; text-transform: uppercase; font-weight: 600;">Startup Profile</p>', unsafe_allow_html=True)
                st.markdown(f"**Industry:** {startup.get('industry', 'N/A')}")
                st.markdown(f"**Core Challenge:** {startup.get('challenges', 'N/A')}")
            
            with col_matches:
                st.markdown('<p style="color: #8b949e; font-size: 0.85em; text-transform: uppercase; font-weight: 600;">Recommended Linkages</p>', unsafe_allow_html=True)
                
                mentor = analysis.get("mentor", {})
                st.markdown(f'**<span class="material-symbols-outlined" style="font-size: 18px;">person</span> Mentor Match:** {mentor.get("name", "N/A")}', unsafe_allow_html=True)
                st.caption(f"{mentor.get('reason', '')}")
                
                if ((st.session_state.linkages_df["Target Startup"] == startup_name) & 
                    (st.session_state.linkages_df["Matched Entity"] == mentor.get('name'))).any():
                    st.success("Mentor Match Approved")
                else:
                    if st.button("Approve Mentor", key=f"app_m_{filename}", type="primary"):
                        approve_linkage(startup_name, mentor.get('name'), "Mentor", mentor.get('reason'))
                        st.rerun()
                
                st.markdown("---")
                
                partner = analysis.get("partner", {})
                st.markdown(f'**<span class="material-symbols-outlined" style="font-size: 18px;">handshake</span> Partner Match:** {partner.get("name", "N/A")}', unsafe_allow_html=True)
                st.caption(f"{partner.get('reason', '')}")
                
                if ((st.session_state.linkages_df["Target Startup"] == startup_name) & 
                    (st.session_state.linkages_df["Matched Entity"] == partner.get('name'))).any():
                    st.success("Partner Match Approved")
                else:
                    if st.button("Approve Partner", key=f"app_p_{filename}", type="primary"):
                        approve_linkage(startup_name, partner.get('name'), "Partner", partner.get('reason'))
                        st.rerun()

st.divider()

# 8. LEDGER
st.markdown('<h3>Approved Ecosystem Linkages</h3>', unsafe_allow_html=True)

if st.session_state.linkages_df.empty:
    st.info("No approved linkages yet.")
else:
    st.dataframe(st.session_state.linkages_df, use_container_width=True, hide_index=True)
    
    csv_export = st.session_state.linkages_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Export to CSV",
        data=csv_export,
        file_name='cradle_ecosystem_ledger.csv',
        mime='text/csv'
    )