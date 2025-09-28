import streamlit as st
import requests
from datetime import datetime
import time
import random
import json  # noqa F401

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Emotional Connect AI",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

DIV_END = '</div>'


# -----------------------------
# Custom CSS for Modern WhatsApp-like UI
# -----------------------------
st.markdown("""
<style>
    /* Main container */
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Header */
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Chat container */
    .chat-container {
        height: 500px;
        overflow-y: auto;
        padding: 1rem;
        background: linear-gradient(to bottom, #f0f2f5, #ffffff);
        border-radius: 15px;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }

    /* Message bubbles */
    .user-message {
        background: linear-gradient(135deg, #25D366, #128C7E);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 5px 18px;
        margin: 8px 0;
        margin-left: 20%;
        max-width: 75%;
        word-wrap: break-word;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        animation: slideInRight 0.3s ease-out;
    }

    .ai-message {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        color: #333;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 5px;
        margin: 8px 0;
        margin-right: 20%;
        max-width: 75%;
        word-wrap: break-word;
        border: 1px solid #e1e5e9;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        animation: slideInLeft 0.3s ease-out;
    }

    /* Animations */
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    @keyframes slideInLeft {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    /* Message timestamp */
    .timestamp {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.7);
        margin-top: 4px;
        text-align: right;
    }

    .timestamp-ai {
        font-size: 0.75rem;
        color: #666;
        margin-top: 4px;
        text-align: left;
    }

    /* Typing indicator */
    .typing-indicator {
        background: #f0f0f0;
        color: #666;
        padding: 8px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-right: 20%;
        max-width: 60%;
        animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }

    /* Input area */
    .input-container {
        background: white;
        padding: 1rem;
        border-radius: 25px;
        border: 2px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    /* Sidebar styling */
    .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }

    /* Status indicators */
    .online-status {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #25D366;
        border-radius: 50%;
        margin-right: 8px;
        animation: blink 2s infinite;
    }

    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #25D366, #128C7E);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Initialize Session State
# -----------------------------
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{random.randint(1000, 9999)}"
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False
    if "ai_personality" not in st.session_state:
        st.session_state.ai_personality = {}


initialize_session_state()

# -----------------------------
# Header
# -----------------------------
st.markdown("""
<div class="header">
    <h1>💬 Emotional Connect AI</h1>
    <p>Your personalized AI companion that understands you</p>
    <span class="online-status"></span>
    <small>AI is online and ready to chat</small>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar Configuration
# -----------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.markdown("### 🎭 AI Personality Settings")

    relationship_type = st.selectbox(
        "👥 Relationship Type",
        ["friend", "mentor", "partner", "mother", "father", "sibling"],
        help="Choose how the AI should relate to you"
    )

    ai_behavior = st.selectbox(
        "🎯 AI Behavior Style",
        ["caring", "funny", "wise", "energetic", "calm", "playful", "romantic", "intellectual", "supportive", "mysterious"],    # noqa: E501
        help="Define the AI's personality traits"
    )

    tier = st.selectbox(
        "⚡ Response Quality",
        ["Basic", "Lite", "Pro"],
        index=2,
        help="Basic: Short replies, Lite: Natural conversation, Pro: Rich & detailed"    # noqa: E501
    )

    st.markdown("### 👤 Personal Settings")

    user_gender = st.selectbox("Your Gender", ["male", "female", "other"])
    ai_gender = st.selectbox("AI Gender", ["female", "male", "other"])

    language = st.selectbox(
        "🗣️ Language",
        ["English", "Hindi", "Marathi", "Tamil", "Telugu", "Bengali"],
        help="Primary language for conversation"
    )

    region = st.text_input("📍 Your Region", "Maharashtra", help="Your location for cultural context")    # noqa: E501

    st.markdown("### 🎨 Chat Customization")

    # Theme selector
    theme = st.selectbox("🎨 Theme", ["Default", "Dark", "Ocean", "Forest"])

    # Emoji quick access
    st.markdown("**Quick Emojis:**")
    emoji_cols = st.columns(4)
    quick_emojis = ["😊", "😂", "❤️", "👍", "😢", "😍", "🤔", "🎉"]

    selected_emoji = ""
    for i, emoji in enumerate(quick_emojis):
        if emoji_cols[i % 4].button(emoji, key=f"emoji_{i}"):
            selected_emoji = emoji

    st.markdown(DIV_END, unsafe_allow_html=True)

    # Chat controls
    st.markdown("### 🔧 Chat Controls")

    if st.button("🗑️ Clear Chat", type="secondary"):
        # Reset conversation with API
        try:
            requests.post("http://127.0.0.1:9000/reset_memory",
                          json={"user_id": st.session_state.user_id})
        except requests.exceptions.RequestException:
            pass

        st.session_state.messages = []
        st.session_state.conversation_started = False
        st.rerun()

    # Export chat
    if st.button("📄 Export Chat"):
        if st.session_state.messages:
            chat_text = "\n".join([f"{msg['sender']} ({msg['time']}): {msg['text']}"     # noqa: E501
                                  for msg in st.session_state.messages])
        st.download_button(
            "Download Chat History",
            chat_text,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",    # noqa: E501
            mime="text/plain"
        )

# -----------------------------
# Main Chat Interface
# -----------------------------
col1, col2 = st.columns([3, 1])

with col1:
    # Chat display area
    chat_container = st.container()

    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # Display welcome message for new conversations
        if not st.session_state.conversation_started and not st.session_state.messages:    # noqa: E501
            st.markdown(f"""
            <div class="ai-message">
                <strong>Welcome! 👋</strong><br>
                I'm your {relationship_type} AI companion with a {ai_behavior} personality.<br>
                I'm here to chat, support, and understand you. What's on your mind?
                <div class="timestamp-ai">{datetime.now().strftime("%H:%M")}</div>
            </div>
            """, unsafe_allow_html=True)

        # Display chat messages
        for msg in st.session_state.messages[-20:]:  # Show last 20 messages
            if msg["sender"] == "You":
                st.markdown(f"""
                <div class="user-message">
                    {msg["text"]}
                    <div class="timestamp">{msg["time"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="ai-message">
                    {msg["text"]}
                    <div class="timestamp-ai">{msg["time"]}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown(DIV_END, unsafe_allow_html=True)

# Input area
st.markdown('<div class="input-container">', unsafe_allow_html=True)

# Create input form
with st.form("chat_form", clear_on_submit=True):
    input_col1, input_col2 = st.columns([4, 1])

    with input_col1:
        user_input = st.text_input(
            "Type your message...",
            placeholder=f"Chat with your {ai_behavior} {relationship_type}...",
            label_visibility="collapsed"
        )

        # Add selected emoji to input
        if selected_emoji:
            user_input += f" {selected_emoji}"

    with input_col2:
        send_button = st.form_submit_button("Send 📤", type="primary")

st.markdown(DIV_END, unsafe_allow_html=True)

# -----------------------------
# Message Processing
# -----------------------------
if send_button and user_input.strip():
    # Add user message
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({
        "sender": "You",
        "text": user_input,
        "time": timestamp
    })

    st.session_state.conversation_started = True

    # Show typing indicator
    typing_placeholder = st.empty()

    with typing_placeholder.container():
        st.markdown("""
        <div class="typing-indicator">
            <strong>AI is typing</strong>
            <span style="animation: blink 1s infinite;">●●●</span>
        </div>
        """, unsafe_allow_html=True)

    # Prepare API payload
    payload = {
        "user_input": user_input,
        "relationship_type": relationship_type,
        "tier": tier,
        "user_id": st.session_state.user_id,
        "region": region,
        "tz": "Asia/Kolkata",
        "user_gender": user_gender,
        "ai_gender": ai_gender,
        "language": language,
        "ai_behavior": ai_behavior
    }

    try:
        # Call backend API
        response = requests.post("http://127.0.0.1:9000/process", json=payload, timeout=10)    # noqa: E501

        if response.status_code == 200:
            data = response.json()
            reply = data["reply"]

            # Simulate realistic typing delay
            typing_delay = data.get("typing_delay", 2.0)
            time.sleep(min(typing_delay, 4.0))  # Cap at 4 seconds

            # Clear typing indicator
            typing_placeholder.empty()

            # Add AI response
            timestamp = datetime.now().strftime("%H:%M")
            st.session_state.messages.append({
                "sender": "AI",
                "text": reply,
                "time": timestamp
            })

        else:
            typing_placeholder.empty()
            error_msg = response.json().get('error', 'Unknown error occurred')
            st.session_state.messages.append({
                "sender": "AI",
                "text": f"Sorry, I'm having technical difficulties: {error_msg}",  # noqa: E501
                "time": datetime.now().strftime("%H:%M")
            })

    except requests.exceptions.Timeout:
        typing_placeholder.empty()
        st.session_state.messages.append({
            "sender": "AI",
            "text": "Sorry, I'm taking too long to respond. Please try again.",
            "time": datetime.now().strftime("%H:%M")
        })

    except requests.exceptions.ConnectionError:
        typing_placeholder.empty()
        st.session_state.messages.append({
            "sender": "AI",
            "text": "🔌 Connection error! Make sure the backend server is running on port 9000.",   # noqa: E501
            "time": datetime.now().strftime("%H:%M")
        })

    except Exception as e:
        typing_placeholder.empty()
        st.session_state.messages.append({
            "sender": "AI",
            "text": f"Unexpected error: {str(e)}",
            "time": datetime.now().strftime("%H:%M")
        })

    # Refresh the page to show new messages
    st.rerun()

# -----------------------------
# Statistics Sidebar
# -----------------------------
with col2:
    st.markdown("### 📊 Chat Stats")

    # Conversation statistics
    total_messages = len(st.session_state.messages)
    user_messages = len([m for m in st.session_state.messages if m["sender"] == "You"])    # noqa: E501
    ai_messages = len([m for m in st.session_state.messages if m["sender"] == "AI"])    # noqa: E501

    st.metric("Total Messages", total_messages)
    st.metric("Your Messages", user_messages)
    st.metric("AI Responses", ai_messages)

    # Current AI personality display
    st.markdown("### 🤖 Current AI")
    st.markdown(f"""
    **Type:** {relationship_type.title()}
    **Behavior:** {ai_behavior.title()}
    **Quality:** {tier}
    **Language:** {language}
    """)

    # Connection status
    st.markdown("### 🔗 Status")
    try:
        health_response = requests.get("http://127.0.0.1:9000/health", timeout=3)   # noqa: E501
        if health_response.status_code == 200:
            st.success("✅ Backend Connected")
            health_data = health_response.json()
            st.caption(f"Active users: {health_data.get('active_users', 0)}")
        else:
            st.error("❌ Backend Error")
    except requests.exceptions.RequestException:
        st.error("❌ Backend Offline")
        st.caption("Start the backend with: `python app.py`")

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <small>
        💡 <strong>Tips:</strong> Be specific about your needs • Use natural language   # noqa: E501
        The AI learns from your conversation style<br>
        🔒 Your conversations are private and stored temporarily for context
    </small>
</div>
""", unsafe_allow_html=True)

# Auto-scroll to bottom (JavaScript injection)
st.markdown("""
<script>
    var chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
</script>
""", unsafe_allow_html=True)
