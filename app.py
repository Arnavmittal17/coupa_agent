import streamlit as st
from dotenv import load_dotenv
import os
import uuid
import plotly.io as pio
from langchain_core.messages import HumanMessage
from agent import get_agent
import time
import re
from tools import get_pending_charts

# Load environment variables
load_dotenv()

# Streamlit Page Config
st.set_page_config(
    page_title="Coupa Data Assistant", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for KPMG styling
st.markdown("""
<style>
    /* Main color scheme - KPMG Blue & White */
    :root {
        --kpmg-blue: #0091DA;
        --kpmg-dark-blue: #00338D;
        --kpmg-light-blue: #E8F4FD;
        --kpmg-gray: #F0F2F6;
        --kpmg-text: #333333;
    }
    
    /* Chat message styling */
    .user-bubble {
        background: linear-gradient(135deg, #0091DA 0%, #00338D 100%);
        padding: 12px 16px;
        border-radius: 18px;
        color: white !important;
        display: inline-block;
        max-width: 80%;
        margin: 5px 0;
    }
    
    .ai-bubble {
        background: #F0F2F6;
        padding: 12px 16px;
        border-radius: 18px;
        color: #333333;
        margin: 5px 0;
    }
    
    /* Prompt suggestion button styling */
    .stButton button {
        height: 80px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        white-space: normal !important;
        word-break: break-word !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        padding: 0.5rem !important;
        line-height: 1.4 !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        border: 2px solid #0091DA !important;
        background-color: white !important;
        color: #333333 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        border-color: #00338D !important;
        background-color: #E8F4FD !important;
        color: #00338D !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,145,218,0.2) !important;
    }
    
    /* Sidebar styling - reduced spacing */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #00338D 0%, #001f5c 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .element-container {
        margin-bottom: -10px !important;
    }
    
    [data-testid="stSidebar"] hr {
        margin: 10px 0 !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        margin-bottom: 5px !important;
        margin-top: 5px !important;
    }
    
    [data-testid="stSidebar"] .stButton button {
        background-color: #0091DA !important;
        color: white !important;
        border: none !important;
        height: 45px !important;
    }
    
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: white !important;
        color: #00338D !important !important;
        transform: scale(1.02) !important;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #0091DA;
        padding: 10px 20px;
    }
    
    /* Status indicators */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 2px 0;
    }
    
    .status-active {
        background: #00C853;
        color: white;
    }
    
    .status-inactive {
        background: #FF5252;
        color: white;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #F0F2F6;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #0091DA;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00338D;
    }
    
    /* Fixed prompts section */
    .prompts-section {
        margin-bottom: 20px;
        padding: 10px;
        background: white;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Function to render suggestion buttons (always visible)
def render_suggestion_buttons(suggestions: list[dict]):
    st.markdown("#### 💡 Quick Questions")
    st.markdown("Click any button below to ask a question:")
    
    result = None
    num_suggestions = len(suggestions)
    
    if num_suggestions == 0:
        return None
    
    # Create 2x2 grid
    col1, col2 = st.columns(2)
    
    for i, suggestion in enumerate(suggestions):
        if i % 2 == 0:
            with col1:
                if st.button(suggestion['text'], use_container_width=True, key=f"suggestion_{i}"):
                    result = suggestion['text']
        else:
            with col2:
                if st.button(suggestion['text'], use_container_width=True, key=f"suggestion_{i}"):
                    result = suggestion['text']
    
    return result

# Custom header with logo at top left
col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    try:
        st.image("logo.png", width=120)
    except FileNotFoundError:
        st.markdown("<h2 style='color: #00338D;'>🏢 KPMG</h2>", unsafe_allow_html=True)

with col2:
    st.markdown("<h1 style='text-align: center; color: #00338D; margin: 0;'>📊 Coupa Data Assistant</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666; margin-top: -5px;'>Intelligent Supplier & Forms Data Analysis</p>", unsafe_allow_html=True)

st.markdown("---")

# Sidebar with reduced spacing
with st.sidebar:
    st.markdown("## 🤖 Assistant")
    st.markdown("---")
    
    # New Chat Button
    def clear_chat():
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        if "agent" in st.session_state:
            del st.session_state.agent
    
    if st.button("✨ New Conversation", use_container_width=True, type="primary", on_click=clear_chat):
        st.rerun()
    
    st.markdown("---")
    
    # Session info
    st.markdown("### 📌 Session")
    session_id = st.session_state.get("thread_id", "Not started")
    st.caption(f"ID: {str(session_id)[:8]}...")
    
    st.markdown("---")
    
    # LangSmith Integration
    st.markdown("### 🔍 LangSmith")
    langsmith_url = "https://smith.langchain.com/"
    st.markdown(f'<a href="{langsmith_url}" target="_blank" style="display: inline-block; padding: 0.4em 1em; background-color: #0091DA; color: white !important; text-decoration: none; border-radius: 4px; font-weight: bold; text-align: center; width: 100%; margin: 5px 0;">View Traces</a>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # System Status
    st.markdown("### ⚡ Status")
    langsmith_api_key = os.environ.get("LANGCHAIN_API_KEY")
    if os.environ.get("LANGCHAIN_TRACING_V2") == "true" and langsmith_api_key and langsmith_api_key != "your_langchain_api_key_here":
        st.markdown('<span class="status-badge status-active">● LangSmith Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-inactive">● LangSmith Inactive</span>', unsafe_allow_html=True)
    
    api_key_check = os.environ.get("OPENAI_API_KEY")
    if api_key_check and api_key_check != "your_openai_api_key_here":
        st.markdown('<span class="status-badge status-active" style="background: #0091DA;">● API Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-inactive">● API Missing</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Help section
    with st.expander("ℹ️ Help"):
        st.caption("Ask about suppliers, forms, or data statistics")
    
    st.markdown("---")
    st.caption("© 2024 KPMG")

# Check API Key
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key or api_key == "your_openai_api_key_here":
    st.warning("⚠️ Please set your OPENAI_API_KEY in the `.env` file to continue.")
    st.stop()

# Initialize session state variables
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# We store the agent in session state
if "agent" not in st.session_state:
    with st.spinner("🔄 Initializing Agent..."):
        st.session_state.agent = get_agent()

# Define suggestions
suggestions = [
    {"text": "what is the distribution of the overall status of the supplier request?"},
    {"text": "What is the completion rate for form 2?"},
    {"text": "Show me suppliers who submitted forms in the last 7 days"},
    {"text": "Give me a summary of all form submissions"}
]

# Friendly labels for tool status indicators
_TOOL_STATUS = {
    "sql_db_list_tables": ("🔍", "Discovering tables..."),
    "sql_db_schema":      ("📋", "Reading table schema..."),
    "sql_db_query":       ("⚡", "Running SQL query..."),
    "sql_db_query_checker": ("✅", "Validating query..."),
    "generate_chart":     ("📊", "Generating chart..."),
    "send_resend_email":  ("📧", "Sending email..."),
}

# Function to handle messages
def handle_message(prompt: str):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble fade-in">{prompt}</div>', unsafe_allow_html=True)

    # Prepare configuration for LangGraph
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    # Get AI response with streaming
    with st.chat_message("assistant"):
        # Status placeholder for tool activity indicators
        status_placeholder = st.empty()
        # Container for the streamed text response
        response_container = st.empty()

        collected_tokens: list[str] = []

        try:
            for msg, _metadata in st.session_state.agent.stream(
                {"messages": [("user", prompt)]},
                config=config,
                stream_mode="messages",
            ):
                msg_type = type(msg).__name__

                if msg_type == "AIMessageChunk":
                    tool_calls = getattr(msg, "tool_calls", [])

                    if tool_calls:
                        # Show a status indicator for the tool being invoked
                        for tc in tool_calls:
                            tc_name = tc.get("name", "")
                            if tc_name:
                                icon, label = _TOOL_STATUS.get(
                                    tc_name, ("⏳", f"Running {tc_name}...")
                                )
                                status_placeholder.info(f"{icon}  {label}")
                    else:
                        # Stream the AI text token-by-token
                        token = getattr(msg, "content", "")
                        if token:
                            # Clear tool status once text starts flowing
                            status_placeholder.empty()
                            collected_tokens.append(token)
                            response_container.markdown("".join(collected_tokens) + "▌")

                elif msg_type == "ToolMessage":
                    # Tool finished — update status briefly
                    name = getattr(msg, "name", "")
                    icon, label = _TOOL_STATUS.get(name, ("✅", ""))
                    if label:
                        done_label = label.replace("...", " ✓")
                        status_placeholder.success(f"{icon}  {done_label}")

            # Clear any remaining status
            status_placeholder.empty()

            # Final response text (remove cursor)
            final_text = "".join(collected_tokens)
            response_container.markdown(final_text)

            # Drain charts from the side-channel buffer
            chart_jsons = get_pending_charts()
            for chart_json in chart_jsons:
                try:
                    fig = pio.from_json(chart_json)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    pass

            # Save to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_text,
                "charts": chart_jsons,
            })

        except Exception as e:
            status_placeholder.empty()
            error_msg = f"❌ Error: {str(e)}"
            response_container.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ===== MAIN CONTENT AREA =====

# Always show prompt suggestions at the top (they remain visible)
suggestion_prompt = render_suggestion_buttons(suggestions)

# Check if a suggestion was clicked
if suggestion_prompt:
    handle_message(suggestion_prompt)
    st.rerun()

# Add a separator between prompts and chat history
if st.session_state.messages:
    st.markdown("---")
    st.markdown("#### 💬 Conversation History")

# Display chat messages from history
for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    
    with st.chat_message(role):
        if role == "user":
            st.markdown(f'<div class="user-bubble fade-in">{content}</div>', unsafe_allow_html=True)
        else:
            # Re-render any saved Plotly charts
            for chart_json in message.get("charts", []):
                try:
                    fig = pio.from_json(chart_json)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    pass
            # Format assistant response
            st.markdown(content)

# Accept user input
if prompt := st.chat_input("💬 Ask about Coupa data... (e.g., 'How many suppliers filled form 1?')"):
    handle_message(prompt)
    st.rerun()