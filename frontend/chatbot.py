import streamlit as st
import requests
from datetime import datetime
import time

st.set_page_config(
    page_title="Emotional Connect AI 🤖",
    page_icon="🤖",
    layout="wide"
)

st.title("Emotional Connect AI 🤖")
st.write("Chat with your personalized AI companion!")

# -----------------------------
# Sidebar options
# -----------------------------
relationship_type = st.sidebar.selectbox(
    "Choose Relationship Type",
    ["friend", "mentor", "partner", "mother", "father", "sibling"]
)
tier = st.sidebar.selectbox("AI Tier", ["Basic", "Lite", "Pro"])
user_gender = st.sidebar.selectbox("Your Gender", ["male", "female", "other"])
ai_gender = st.sidebar.selectbox("AI Gender", ["female", "male", "other"])
region = st.sidebar.text_input("Your Region", "Maharashtra")
tz = st.sidebar.text_input("Timezone", "Asia/Kolkata")

# Emoji picker
emoji = st.sidebar.selectbox("Add Emoji", ["", "😊", "😂", "😍", "😎", "👍", "🤖"])

# -----------------------------
# Session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []

# -----------------------------
# User input
# -----------------------------
user_input = st.text_input("Type your message here:", key="input")
if emoji:
    user_input += " " + emoji

# -----------------------------
# Send message
# -----------------------------
if st.button("Send") and user_input:
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"sender": "You", "text": user_input, "time": timestamp})  # noqa: E501

    # Show AI typing animation
    typing_placeholder = st.empty()
    typing_text = "AI is typing"
    for i in range(3):
        typing_placeholder.markdown(f"**{typing_text}{'.'*(i+1)}**")
        time.sleep(0.5)

    # Call backend API
    payload = {
        "user_input": user_input,
        "relationship_type": relationship_type,
        "tier": tier,
        "user_id": "user_001",
        "region": region,
        "tz": tz,
        "user_gender": user_gender,
        "ai_gender": ai_gender
    }
    try:
        response = requests.post("http://127.0.0.1:9000/process", json=payload)
        if response.status_code == 200:
            reply = response.json()["reply"]
        else:
            reply = f"Error: {response.json().get('error', 'Unknown')}"
    except Exception as e:
        reply = f"Failed to connect to API: {e}"

    typing_placeholder.empty()
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"sender": "AI", "text": reply, "time": timestamp})  # noqa: E501


# -----------------------------
# Chat display (WhatsApp style, no big box)
# -----------------------------
chat_style = """
<style>
.user-msg, .ai-msg {
    padding: 10px;
    border-radius: 15px;
    margin: 5px 0px;
    max-width: 70%;
    word-wrap: break-word;
    display: inline-block;
}
.user-msg {
    background-color: #DCF8C6;
    color: black;
    text-align: right;
    float: right;
    clear: both;
}
.ai-msg {
    background-color: #FFFFFF;
    color: black;
    text-align: left;
    float: left;
    clear: both;
}
.time {
    font-size: 10px;
    color: gray;
    margin-left: 5px;
}
.clearfix {
    clear: both;
}
</style>
"""
st.markdown(chat_style, unsafe_allow_html=True)

for msg in st.session_state.messages[-20:]:
    if msg["sender"] == "You":
        st.markdown(
            f'<div class="user-msg">{msg["text"]} <span class="time">{msg["time"]}</span></div>'    # noqa: E501
            '<div class="clearfix"></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="ai-msg">{msg["text"]} <span class="time">{msg["time"]}</span></div>'    # noqa: E501
            '<div class="clearfix"></div>',
            unsafe_allow_html=True
        )
