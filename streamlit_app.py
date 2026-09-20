import streamlit as st
import requests

# Configuration
API_URL = "https://first-python-q0wh.onrender.com"

# Page configuration
st.set_page_config(
    page_title="Zunzu AI Assistant",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS for beautiful styling
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stTextInput > div > div > input {
        background-color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("🧠 Zunzu AI Assistant")
st.markdown("### Your Intelligent AI with Memory")
st.markdown("---")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response from your FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": prompt},
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                ai_answer = data["ai_answer"]
                
                st.markdown(ai_answer)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": ai_answer})
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Sidebar with controls
with st.sidebar:
    st.header("⚙️ Controls")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Session Stats")
    st.metric("Messages", len(st.session_state.messages))
    
    st.markdown("---")
    st.markdown("### 🔗 Quick Links")
    st.markdown("- [API Documentation](https://first-python-q0wh.onrender.com/docs)")
    st.markdown("- [View History](https://first-python-q0wh.onrender.com/history)")
    
    st.markdown("---")
    st.markdown("### 👨‍💻 Built by")
    st.markdown("**Master Zunzu**")
    st.markdown("AI Engineer in Training")