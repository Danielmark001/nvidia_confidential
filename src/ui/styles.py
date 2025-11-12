"""
Centralized CSS styling for Streamlit UI components.
"""

CUSTOM_CSS = """
<style>
    .stApp {
        max-width: 100%;
    }

    .main {
        max-width: 1000px;
        margin: 0 auto;
    }

    [data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 350px !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        width: 350px !important;
    }

    .main-header {
        text-align: center;
        padding: 1rem 0 2rem 0;
        border-bottom: 2px solid #e8eef7;
        margin-bottom: 2rem;
    }

    .main-header h1 {
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }

    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .status-success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }

    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }

    .info-box {
        background: linear-gradient(135deg, #f0f4ff 0%, #f8fbff 100%);
        border-left: 4px solid #1f77b4;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(31, 119, 180, 0.08);
    }

    [data-testid="stChatMessageContent"] {
        padding: 1rem;
        border-radius: 8px;
    }

    .main > div:last-child {
        padding-bottom: 150px;
    }

    .input-wrapper {
        position: fixed !important;
        bottom: 0 !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 100% !important;
        max-width: 800px !important;
        background-color: white !important;
        z-index: 1000 !important;
        padding: 1.5rem 2rem !important;
        box-shadow: 0 -2px 20px rgba(0, 0, 0, 0.08) !important;
    }

    [data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 350px !important;
        width: calc(100% - 350px) !important;
        max-width: 750px !important;
        background-color: white !important;
        z-index: 1000 !important;
        padding: 1.5rem 2rem 2rem 2rem !important;
        box-shadow: 0 -2px 20px rgba(0, 0, 0, 0.08) !important;
        margin: 0 !important;
        margin-left: 4rem !important;
    }

    [data-testid="stChatInput"] input {
        background-color: #ffffff !important;
        border: 5px solid #667eea !important;
        border-radius: 50px !important;
        padding: 2rem 3rem !important;
        font-size: 1.4rem !important;
        color: #000000 !important;
        font-weight: 700 !important;
        box-shadow: 0 6px 24px rgba(102, 126, 234, 0.25) !important;
        transition: all 0.3s ease !important;
        min-height: 70px !important;
    }

    [data-testid="stChatInput"] input:focus {
        border-color: #667eea !important;
        background-color: white !important;
        outline: none !important;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35) !important;
        transform: translateY(-3px) !important;
    }

    [data-testid="stFileUploader"] {
        position: fixed !important;
        bottom: 2rem !important;
        right: 2rem !important;
        z-index: 1001 !important;
    }

    [data-testid="stFileUploader"] section {
        padding: 0.8rem 1.2rem !important;
        border: 2px solid #667eea !important;
        border-radius: 24px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        transition: all 0.3s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3) !important;
    }

    [data-testid="stFileUploader"] section:hover {
        background: linear-gradient(135deg, #5568d3 0%, #6a4091 100%) !important;
        box-shadow: 0 5px 18px rgba(102, 126, 234, 0.45) !important;
        transform: translateY(-2px) !important;
    }

    [data-testid="stFileUploader"] button {
        font-size: 0.95rem !important;
        padding: 0.2rem 0.5rem !important;
        background: transparent !important;
        border: none !important;
        transition: all 0.3s !important;
        cursor: pointer !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px !important;
    }

    [data-testid="stFileUploader"] button:hover {
        background: transparent !important;
        color: #ffffff !important;
    }

    [data-testid="stFileUploader"] button span {
        display: block !important;
        color: #ffffff !important;
    }

    [data-testid="stFileUploader"] button * {
        color: #ffffff !important;
    }

    [data-testid="stFileUploader"] button::before {
        content: "" !important;
        display: none !important;
    }

    [data-testid="stFileUploader"] label {
        display: none !important;
    }

    [data-testid="stFileUploader"] small {
        color: #ffffff !important;
        font-size: 0.8rem !important;
    }

    [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] {
        color: #ffffff !important;
    }

    [data-testid="stFileUploader"] p {
        color: #ffffff !important;
    }

    [data-testid="stFileUploader"] div {
        color: #ffffff !important;
    }

    [data-testid="stChatInput"] input::placeholder {
        color: #95a5a6 !important;
        font-weight: 400 !important;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }

    .stDivider {
        margin: 1.5rem 0;
    }
</style>
"""


def apply_custom_styling():
    """Apply custom CSS styling to the Streamlit app."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
