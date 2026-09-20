import streamlit as st
import requests

API_URL = "https://first-python-q0wh.onrender.com" # Replace with your actual Render backend URL

st.set_page_config(page_title="Zunzu AI Assistant (RAG)", page_icon="🧠", layout="wide")

st.title("🧠 Zunzu AI Assistant with RAG")
st.markdown("Upload a PDF document, then ask questions specifically about its contents!")

# Sidebar for PDF Upload
with st.sidebar:
    st.header("📄 Knowledge Base")
    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
    
    if uploaded_file is not None:
        with st.spinner("Reading and embedding PDF... (This may take 10-20 seconds)"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            try:
                response = requests.post(f"{API_URL}/upload_pdf", files=files)
                if response.status_code == 200:
                    st.success(response.json()["message"])
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Failed to upload: {str(e)}")
    
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your uploaded PDF..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking and searching documents..."):
            try:
                response = requests.post(f"{API_URL}/ask", json={"question": prompt}, timeout=30)
                response.raise_for_status()
                data = response.json()
                ai_answer = data["ai_answer"]
                
                st.markdown(ai_answer)
                st.session_state.messages.append({"role": "assistant", "content": ai_answer})
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})