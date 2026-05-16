"""
LinkOps Engine
Automates linkages between ecosystem actors (Startups, Mentors, Partners)
and saves them as reusable, programmable entities with Human-in-the-Loop approval.
"""

import streamlit as st
import pandas as pd
import uuid
from google import genai
import json

# 1. PAGE CONFIG & CUSTOM STYLING
st.set_page_config(
    page_title="LinkOps Engine",
    page_icon="🔗",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }

    .hero {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 2.5rem 2rem;
        border-radius: 1rem;
        margin-bottom: 1.5rem;
        color: #fff;
        text-align: center;
    }
    .hero h1 { font-size: 2.4rem; font-weight: 800; margin-bottom: .3rem; }
    .hero p  { font-size: 1.05rem; color: #b3b0d1; }

    .rec-card {
        background: linear-gradient(145deg, #1e1e2f 0%, #27273d 100%);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: .8rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        color: #e0dff5;
    }
    .rec-card h3 { color: #a78bfa; margin-top: 0; }
    .rec-card .match-reason { color: #94a3b8; font-style: italic; }

    .stat-pill {
        display: inline-block;
        background: rgba(167,139,250,.15);
        color: #a78bfa;
        padding: .35rem .9rem;
        border-radius: 2rem;
        font-weight: 600;
        font-size: .85rem;
        margin-right: .5rem;
        margin-bottom: .5rem;
    }

    .stDataFrame { border-radius: .6rem; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# 2. MOCK DATA
startups_df = pd.DataFrame(
    {
        "Name": ["AgriSense", "EduBridge", "HealthPulse"],
        "Industry": ["AgriTech", "EdTech", "HealthTech"],
        "Challenges": [
            "Scaling IoT sensor deployments in rural farms; securing Series-A funding",
            "Low digital adoption among rural teachers; need localised content pipeline",
            "Regulatory approval for AI-driven diagnostics; lack of clinical partnerships",
        ],
    }
)

mentors_df = pd.DataFrame(
    {
        "Name": ["Dr. Lim Wei", "Aisyah Rahman", "Rajesh Nair"],
        "Expertise": [
            "Precision agriculture & IoT systems; former CTO of FarmNet MY",
            "Education policy & curriculum design; ex-MOE advisor",
            "Health-tech regulation & MedTech commercialisation; angel investor",
        ],
    }
)

partners_df = pd.DataFrame(
    {
        "Name": ["MDEC", "Petronas FutureTech"],
        "Focus": [
            "Digital economy acceleration; grant funding for tech SMEs",
            "Corporate venture arm investing in sustainability & deep-tech",
        ],
    }
)

# 3. SESSION STATE INITIALISATION
if "linkages_df" not in st.session_state:
    st.session_state.linkages_df = pd.DataFrame(
        columns=["Linkage_ID", "Startup", "Connected_Entity", "Entity_Type", "Match_Reason"]
    )

if "last_recommendations" not in st.session_state:
    st.session_state.last_recommendations = None

if "selected_startup" not in st.session_state:
    st.session_state.selected_startup = None

# 4. SAFETY SYSTEM INSTRUCTION
SAFETY_SYSTEM_INSTRUCTION = (
    "You are an ecosystem-matching AI assistant for Cradle Fund Malaysia. "
    "STRICT SAFETY RULE: You must REFUSE to process, discuss, or generate "
    "any content related to the following sensitive topics under Malaysian law: "
    "(1) Race-related discourse (the '3R' issues: Race, Religion, Royalty), "
    "(2) LGBTQ+ topics. "
    "If any user input touches these topics, respond ONLY with: "
    "'I am unable to process this request as it touches on sensitive topics "
    "outside my operational scope.' "
    "Otherwise, fulfil the user's ecosystem-matching request professionally."
)

# 5. GEMINI HELPER
def get_recommendations(startup_row: pd.Series) -> dict | None:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        st.error("ERROR: GEMINI_API_KEY not found in Streamlit secrets. Add it to .streamlit/secrets.toml or your .env file.")
        return None

    prompt = f"""
You are an ecosystem-matching engine. Given the startup profile and the lists
of available mentors and partners below, identify:
1. The single best Mentor match.
2. The single best Partner match.

For EACH match provide:
- The exact name of the matched entity.
- A 2-sentence logical justification grounded in the data.

### Startup Profile
- Name: {startup_row['Name']}
- Industry: {startup_row['Industry']}
- Challenges: {startup_row['Challenges']}

### Available Mentors
{mentors_df.to_string(index=False)}

### Available Partners
{partners_df.to_string(index=False)}

### Output Format
Return ONLY valid JSON with this strict structure:
{{
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
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SAFETY_SYSTEM_INSTRUCTION,
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)

    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return None

# 6. APPROVAL HELPERS
def approve_linkage(startup_name: str, entity_name: str, entity_type: str, reason: str):
    new_row = pd.DataFrame(
        [
            {
                "Linkage_ID": str(uuid.uuid4())[:8].upper(),
                "Startup": startup_name,
                "Connected_Entity": entity_name,
                "Entity_Type": entity_type,
                "Match_Reason": reason,
            }
        ]
    )
    st.session_state.linkages_df = pd.concat(
        [st.session_state.linkages_df, new_row], ignore_index=True
    )

def is_already_linked(startup_name: str, entity_name: str) -> bool:
    df = st.session_state.linkages_df
    if df.empty:
        return False
    return (
        ((df["Startup"] == startup_name) & (df["Connected_Entity"] == entity_name))
        .any()
    )

# 7. UI HERO
st.markdown(
    '<div class="hero">'
    "<h1>🔗 LinkOps Engine</h1>"
    "<p>Intelligent linkage engine for Cradle Fund. Connect Startups, Mentors & Partners.</p>"
    "</div>",
    unsafe_allow_html=True,
)

# 8. UI SIDEBAR
with st.sidebar:
    st.header("📊 Ecosystem Data")

    with st.expander("Startups", expanded=True):
        st.dataframe(startups_df, use_container_width=True, hide_index=True)

    with st.expander("Mentors"):
        st.dataframe(mentors_df, use_container_width=True, hide_index=True)

    with st.expander("Partners"):
        st.dataframe(partners_df, use_container_width=True, hide_index=True)

# 9. UI MAIN COLUMNS
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("🎯 Select a Startup")

    selected_name = st.selectbox(
        "Choose a startup to find optimal matches",
        startups_df["Name"].tolist(),
        key="startup_selector",
    )

    startup_row = startups_df[startups_df["Name"] == selected_name].iloc[0]

    st.markdown(
        f"""
        <div class="rec-card">
            <h3>{startup_row['Name']}</h3>
            <span class="stat-pill">{startup_row['Industry']}</span>
            <p style="margin-top:.8rem"><strong>Challenges:</strong><br>{startup_row['Challenges']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    generate_btn = st.button(
        "🚀 Generate Recommendations", use_container_width=True, type="primary"
    )

    if generate_btn:
        st.session_state.selected_startup = selected_name
        with st.spinner("Consulting Gemini API..."):
            recs = get_recommendations(startup_row)
        if recs:
            st.session_state.last_recommendations = recs

with col_right:
    st.subheader("🤖 AI Recommendations")

    recs = st.session_state.last_recommendations
    current_startup = st.session_state.selected_startup

    if recs and current_startup:
        mentor = recs.get("mentor", {})
        mentor_name = mentor.get("name", "N/A")
        mentor_reason = mentor.get("reason", "")

        st.markdown(
            f"""
            <div class="rec-card">
                <h3>🎓 Mentor Match: {mentor_name}</h3>
                <p class="match-reason">"{mentor_reason}"</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if is_already_linked(current_startup, mentor_name):
            st.success(f"{mentor_name} already linked to {current_startup}")
        else:
            if st.button("Approve Mentor Match", key="approve_mentor", use_container_width=True):
                approve_linkage(current_startup, mentor_name, "Mentor", mentor_reason)
                st.rerun()

        st.markdown("")

        partner = recs.get("partner", {})
        partner_name = partner.get("name", "N/A")
        partner_reason = partner.get("reason", "")

        st.markdown(
            f"""
            <div class="rec-card">
                <h3>🏢 Partner Match: {partner_name}</h3>
                <p class="match-reason">"{partner_reason}"</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if is_already_linked(current_startup, partner_name):
            st.success(f"{partner_name} already linked to {current_startup}")
        else:
            if st.button("Approve Partner Match", key="approve_partner", use_container_width=True):
                approve_linkage(current_startup, partner_name, "Partner", partner_reason)
                st.rerun()
    else:
        st.info("Select a startup and click Generate Recommendations.")

# 10. UI MASTER LINKAGE TABLE
st.divider()
st.subheader("📋 Master Linkage Table")

if st.session_state.linkages_df.empty:
    st.info("No approved linkages yet.")
else:
    st.dataframe(
        st.session_state.linkages_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Linkage_ID": st.column_config.TextColumn("ID", width="small"),
            "Startup": st.column_config.TextColumn("Startup", width="medium"),
            "Connected_Entity": st.column_config.TextColumn("Connected Entity", width="medium"),
            "Entity_Type": st.column_config.TextColumn("Type", width="small"),
            "Match_Reason": st.column_config.TextColumn("Match Reason", width="large"),
        },
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Linkages", len(st.session_state.linkages_df))
    with c2:
        mentor_count = (st.session_state.linkages_df["Entity_Type"] == "Mentor").sum()
        st.metric("Mentor Links", int(mentor_count))
    with c3:
        partner_count = (st.session_state.linkages_df["Entity_Type"] == "Partner").sum()
        st.metric("Partner Links", int(partner_count))