# import streamlit as st
# from dotenv import load_dotenv
# import os
# import uuid
# from langchain_core.messages import HumanMessage
# from agent import get_agent

# # Load environment variables
# load_dotenv()

# # Streamlit Page Config
# st.set_page_config(page_title="Coupa Data Assistant", page_icon="📊", layout="wide")

# # Custom UI adjustments
# st.markdown("""
# <style>
#     .trace-btn {
#         display: inline-block;
#         padding: 0.5em 1em;
#         background-color: #0091DA;
#         color: white !important;
#         text-decoration: none;
#         border-radius: 4px;
#         font-weight: bold;
#         text-align: center;
#         width: 100%;
#         margin-top: 10px;
#     }
#     .trace-btn:hover {
#         background-color: #005eb8;
#         color: white !important;
#     }
    
#     /* User Chat Message Styling */
#     [data-testid="stChatMessage"]:has(.user-msg) {
#         background-color: #0091DA !important;
#         border-radius: 10px;
#         color: white !important;
#     }
#     [data-testid="stChatMessage"]:has(.user-msg) [data-testid="stMarkdownContainer"] p {
#         color: white !important;
#     }
    
#     /* Sidebar Styling */
#     [data-testid="stSidebar"] {
#         background-color: #00338D !important;
#     }
#     [data-testid="stSidebar"] * {
#         color: white !important;
#     }
# </style>
# """, unsafe_allow_html=True)

# with st.sidebar:
#     # Logo
#     try:
#         st.image("logo.png", width=150)
#     except FileNotFoundError:
#         st.markdown("<h2 style='color: white;'>KPMG</h2>", unsafe_allow_html=True)
        
#     st.markdown("---")
    
#     # New Chat Button
#     if st.button("➕ New Chat", use_container_width=True, type="primary"):
#         st.session_state.thread_id = str(uuid.uuid4())
#         st.session_state.messages = []
#         if "agent" in st.session_state:
#             del st.session_state.agent
#         st.rerun()
        
#     st.markdown("---")
#     st.markdown("<h3 style='color: white;'>LangSmith Traceability</h3>", unsafe_allow_html=True)
#     langsmith_url = "https://smith.langchain.com/"
#     st.markdown(f'<a href="{langsmith_url}" target="_blank" class="trace-btn">🔍 View Traces</a>', unsafe_allow_html=True)
    
#     st.markdown("---")
#     st.markdown("<h3 style='color: white;'>System Status</h3>", unsafe_allow_html=True)
#     # LangSmith Integration Status
#     langsmith_api_key = os.environ.get("LANGCHAIN_API_KEY")
#     if os.environ.get("LANGCHAIN_TRACING_V2") == "true" and langsmith_api_key and langsmith_api_key != "your_langchain_api_key_here":
#         st.success("✅ LangSmith Tracking: Active")
#     else:
#         st.warning("⚠️ LangSmith Inactive. Add `LANGCHAIN_API_KEY` and `LANGCHAIN_TRACING_V2=true` to `.env`")

# st.title("📊 Coupa Data Assistant")
# st.write("Ask questions about the Coupa supplier and forms data!")

# # Check API Key
# api_key = os.environ.get("OPENAI_API_KEY")
# if not api_key or api_key == "your_openai_api_key_here":
#     st.warning("⚠️ Please set your OPENAI_API_KEY in the `.env` file to continue.")
#     st.stop()

# # Initialize session state variables
# if "thread_id" not in st.session_state:
#     st.session_state.thread_id = str(uuid.uuid4())

# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # We store the agent in session state so the MemorySaver checkpointer is preserved across Streamlit reruns.
# if "agent" not in st.session_state:
#     with st.spinner("Initializing Agent..."):
#         st.session_state.agent = get_agent()

# # Display chat messages from history on app rerun
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         if message["role"] == "user":
#             st.markdown(f'<div class="user-msg">{message["content"]}</div>', unsafe_allow_html=True)
#         else:
#             st.markdown(message["content"])

# # React to user input
# if prompt := st.chat_input("E.g., How many suppliers have filled form 1?"):
#     # Display user message in chat message container
#     with st.chat_message("user"):
#         st.markdown(f'<div class="user-msg">{prompt}</div>', unsafe_allow_html=True)
#     # Add user message to chat history
#     st.session_state.messages.append({"role": "user", "content": prompt})

#     # Prepare configuration for LangGraph (this ties the conversation history to the thread)
#     config = {"configurable": {"thread_id": st.session_state.thread_id}}

#     # Display assistant response in chat message container
#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         with st.spinner("Thinking... (Querying Database)"):
#             try:
#                 # Stream the events from the agent to get the final response
#                 events = st.session_state.agent.stream(
#                     {"messages": [("user", prompt)]},
#                     config=config,
#                     stream_mode="values"
#                 )
                
#                 # Consume the stream to get the final state
#                 final_event = None
#                 for event in events:
#                     final_event = event
                
#                 # The last message in the 'messages' array is the AI's response
#                 final_message = final_event["messages"][-1].content
                
#                 message_placeholder.markdown(final_message)
                
#                 # Add assistant response to chat history
#                 st.session_state.messages.append({"role": "assistant", "content": final_message})
                
#             except Exception as e:
#                 st.error(f"An error occurred: {e}")


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

# Function to handle messages
def handle_message(prompt: str):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(f'<div class="user-bubble fade-in">{prompt}</div>', unsafe_allow_html=True)
    
    # Prepare configuration for LangGraph
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    # Get AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("🤔 Analyzing data..."):
            try:
                # Stream the events from the agent
                events = st.session_state.agent.stream(
                    {"messages": [("user", prompt)]},
                    config=config,
                    stream_mode="values"
                )
                
                # Consume the stream to get the final state
                final_event = None
                for event in events:
                    final_event = event

                # Drain charts from the side-channel buffer
                chart_jsons = get_pending_charts()

                # The last message in the 'messages' array is the AI's response
                final_message = final_event["messages"][-1].content

                # Render any charts that were generated
                for chart_json in chart_jsons:
                    try:
                        fig = pio.from_json(chart_json)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass
                
                # Format the response
                final_message = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', final_message)
                
                message_placeholder.markdown(f'<div class="ai-bubble fade-in">{final_message}</div>', unsafe_allow_html=True)
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_message,
                    "charts": chart_jsons,
                })
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                message_placeholder.error(error_msg)
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
            # Format assistant response
            content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
            st.markdown(f'<div class="ai-bubble fade-in">{content}</div>', unsafe_allow_html=True)

# Accept user input
if prompt := st.chat_input("💬 Ask about Coupa data... (e.g., 'How many suppliers filled form 1?')"):
    handle_message(prompt)
    st.rerun()