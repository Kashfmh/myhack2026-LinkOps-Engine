import os
import json
import streamlit as st
from google import genai
from config import GEMINI_MODEL, XAI_MAX_MSGS, XAI_COOLDOWN_SEC, XAI_MAX_CHARS

SAFETY_SYSTEM_INSTRUCTION = (
    "You are an enterprise decision support AI for Cradle Fund Malaysia. "
    "STRICT SAFETY RULE: Refuse to process any content related to Malaysian 3R issues "
    "(Race, Religion, Royalty) or LGBTQ+ topics. "
)


def execute_match_protocol(uploaded_file, mentors_df, partners_df) -> dict | None:
    api_key = os.environ.get("GEMINI_API_KEY", "")
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
            model=GEMINI_MODEL,
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


def query_xai(analysis: dict, chat_history: list, user_question: str, mentors_df, partners_df):
    # stream xai chunks back to ui
    api_key = os.environ.get("GEMINI_API_KEY", "")
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
            model=GEMINI_MODEL,
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


def approve_linkage(startup_name: str, entity_name: str, entity_type: str, reason: str):
    import pandas as pd
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
