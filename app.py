import streamlit as st
from dotenv import load_dotenv
import os
import uuid
from langchain_core.messages import HumanMessage
from agent import get_agent

# Load environment variables
load_dotenv()

# Streamlit Page Config
st.set_page_config(page_title="Coupa Data Assistant", page_icon="📊", layout="wide")

st.title("📊 Coupa Data Assistant")
st.write("Ask questions about the Coupa supplier and forms data!")

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

# We store the agent in session state so the MemorySaver checkpointer is preserved across Streamlit reruns.
if "agent" not in st.session_state:
    with st.spinner("Initializing Agent..."):
        st.session_state.agent = get_agent()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("E.g., How many suppliers have filled form 1?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare configuration for LangGraph (this ties the conversation history to the thread)
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Thinking... (Querying Database)"):
            try:
                # Stream the events from the agent to get the final response
                events = st.session_state.agent.stream(
                    {"messages": [("user", prompt)]},
                    config=config,
                    stream_mode="values"
                )
                
                # Consume the stream to get the final state
                final_event = None
                for event in events:
                    final_event = event
                
                # The last message in the 'messages' array is the AI's response
                final_message = final_event["messages"][-1].content
                
                message_placeholder.markdown(final_message)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": final_message})
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
