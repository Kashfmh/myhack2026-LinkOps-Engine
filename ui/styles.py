import streamlit as st


def inject_styles():
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


def show_toast(message, type="success"):
    color = "#10b981" if type == "success" else "#ef4444"
    bg    = "#10b9810d" if type == "success" else "#ef44440d"
    icon  = "check_circle" if type == "success" else "error"

    css = f"""
    <style>
    @keyframes toastFadeInOut {{
        0%   {{ opacity: 0; transform: translate(-50%, -20px); }}
        10%  {{ opacity: 1; transform: translate(-50%, 0); }}
        80%  {{ opacity: 1; transform: translate(-50%, 0); }}
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
