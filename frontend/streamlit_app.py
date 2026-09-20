import streamlit as st
import requests
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path 


# --- THE FIX: Find the config.yaml in the same folder as this script ---
# Get the directory where streamlit_app.py is located
current_dir = Path(__file__).parent
config_path = current_dir / "config.yaml"

# 1. Load the User Database
with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

# 2. Initialize the Authenticator (The Bouncer)
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

# 3. Create the Login Widget
name, authentication_status, username = authenticator.login('Login', 'main')

# 4. The Gate: If they are NOT logged in, show nothing but the login box
if authentication_status:
    # --- EVERYTHING INSIDE HERE IS HIDDEN UNTIL THEY LOGIN ---
    authenticator.logout('Logout', 'sidebar')
    
    API_URL = "https://first-python-q0wh.onrender.com" # Replace with your actual Render backend URL

    st.title("🧠 Zunzu AI Assistant (Pro)")
    st.markdown("Welcome, " + name + "! Upload a PDF and ask questions.")

    # Sidebar for PDF Upload
    with st.sidebar:
        st.header("📄 Knowledge Base")
        uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
        
        if uploaded_file is not None:
            with st.spinner("Reading and embedding PDF..."):
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
        st.markdown("### 💎 Subscription Status")
        st.info("You are on the **Free Tier** (3 questions/day).")
        st.markdown("[🚀 **Upgrade to Pro for $10/mo**](https://buy.stripe.com/test_aFa9ALgWi8bG2wS9ymaR200)")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(f"{API_URL}/ask", json={"question": prompt}, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    ai_answer = data["ai_answer"]
                    
                    st.markdown(ai_answer)
                    st.session_state.messages.append({"role": "assistant", "content": ai_answer})
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')