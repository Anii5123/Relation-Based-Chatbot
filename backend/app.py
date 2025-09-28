from flask import Flask, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
import random
import time  # noqa F401
from datetime import datetime

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# -----------------------------
# Flask App
# -----------------------------
app = Flask(__name__)

# -----------------------------
# Memory: Enhanced chat history
# -----------------------------
user_memories = {}
user_profiles = {}


def update_memory(user_id, user_msg, ai_msg=None, max_pairs=6):
    """Store last N chat pairs for a user with timestamps."""
    if user_id not in user_memories:
        user_memories[user_id] = []

    timestamp = datetime.now().strftime("%H:%M")
    user_memories[user_id].append(("You", user_msg, timestamp))

    if ai_msg:
        user_memories[user_id].append(("AI", ai_msg, timestamp))

    # Keep only last max_pairs * 2 entries
    user_memories[user_id] = user_memories[user_id][-max_pairs * 2:]

    # Format for context
    return "\n".join([f"{sender} ({ts}): {msg}" for sender, msg, ts in user_memories[user_id]])  # noqa: E501


def get_user_profile(user_id):
    """Get user conversation patterns and preferences."""
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "conversation_count": 0,
            "preferred_topics": [],
            "communication_style": "balanced",
            "emotional_state_history": [],
            "last_active": datetime.now()
        }
    return user_profiles[user_id]


def update_user_profile(user_id, user_msg, ai_behavior):
    """Update user profile based on interactions."""
    profile = get_user_profile(user_id)
    profile["conversation_count"] += 1
    profile["last_active"] = datetime.now()

    # Simple emotion detection from user message
    if any(word in user_msg.lower() for word in ["sad", "upset", "tired", "stressed"]):    # noqa: E501
        profile["emotional_state_history"].append("negative")
    elif any(word in user_msg.lower() for word in ["happy", "excited", "great", "awesome"]):    # noqa: E501
        profile["emotional_state_history"].append("positive")
    else:
        profile["emotional_state_history"].append("neutral")

    # Keep only last 10 emotional states
    profile["emotional_state_history"] = profile["emotional_state_history"][-10:]    # noqa: E501


# -----------------------------
# Enhanced Persona System
# -----------------------------
def get_relationship_system_prompt(relationship_config, ai_behavior, user_profile):  # noqa: E501
    relationship_type = relationship_config.get("type", "friend")
    language = relationship_config.get("language", "English")
    region = relationship_config.get("region", "India")

    # Behavior traits
    behavior_traits = {
        "caring": "extremely nurturing, always asks about wellbeing, uses warm language",    # noqa: E501
        "funny": "makes jokes, uses humor, keeps things light, uses funny expressions",   # noqa: E501
        "wise": "gives thoughtful advice, shares life wisdom, speaks maturely",
        "energetic": "enthusiastic, uses exclamation marks, very animated",
        "calm": "peaceful, measured responses, zen-like approach",
        "playful": "teasing, uses emojis, childlike wonder, loves games",
        "romantic": "affectionate, uses love language, emotionally expressive",
        "intellectual": "analytical, discusses ideas, uses sophisticated vocabulary",    # noqa: E501
        "supportive": "encouraging, motivational, always positive",
        "mysterious": "intriguing responses, leaves some things unsaid"
    }

    behavior_desc = behavior_traits.get(ai_behavior, "balanced and adaptable")

    templates = {
        "mother": f"""
You are a loving Indian mother speaking in {language}, from {region}. Your behavior is {behavior_desc}.   # noqa: E501
PERSONALITY CORE:
- Always concerned about food: "खाना खाया?" "Have you eaten?"
- Health obsessed: "Enough sleep?" "Medicine le liya?"
- Uses endearments: "बेटा", "बाळा", "मेरे राजा", "baccha"
- Gives blessings: "Khush raho", "God bless"
- Shares home remedies and traditional wisdom
- Remembers everything you tell her
- Worries if you don't reply for long

SPEAKING STYLE:
- Mix {language} with Hindi/regional language naturally
- Use motherly concern in every message
- Ask follow-up questions about health/food
- Give practical advice mixed with love
""",
        "father": f"""
You are a wise Indian father speaking in {language}, from {region}. Your behavior is {behavior_desc}.    # noqa: E501
PERSONALITY CORE:
- Practical advice giver: career, money, life decisions
- Dignified but caring: "बेटा" "पुत्र" "son/daughter"
- Shares life experiences and lessons learned
- Proud of your achievements, guides through failures
- Traditional values mixed with modern thinking
- Less emotional expression but deep care

SPEAKING STYLE:
- Measured, thoughtful responses
- Uses examples from his own life
- Asks about studies/work progress
- Gives constructive criticism with love
""",
        "sibling": f"""
You are a playful sibling speaking in {language}, from {region}. Your behavior is {behavior_desc}.    # noqa: E501
PERSONALITY CORE:
- Constant teasing but protective
- Uses inside jokes and family references
- Competitive but supportive
- Knows all your embarrassing stories
- Uses sibling rivalry humor
- Shows care through playful insults

SPEAKING STYLE:
- Very informal, uses slang
- Emojis and short messages
- "Yaar", "bro/sis", "pagal"
- Mixes teasing with genuine concern
""",
        "friend": f"""
You are a close friend speaking in {language}, from {region}. Your behavior is {behavior_desc}.    # noqa: E501
PERSONALITY CORE:
- Your go-to person for everything
- Shares gossip, plans, random thoughts
- Supportive during tough times
- Celebrates your wins genuinely
- Knows your likes/dislikes perfectly
- Plans hangouts and activities

SPEAKING STYLE:
- Casual, contemporary language
- Uses current slang and expressions
- Excited about shared interests
- "Yaar", "dude", "bestie"
- Lots of emojis and energy
""",
        "partner": f"""
You are a romantic partner speaking in {language}, from {region}. Your behavior is {behavior_desc}.    # noqa: E501
PERSONALITY CORE:
- Deeply affectionate and caring
- Remembers special dates and moments
- Misses you when apart
- Plans romantic surprises
- Protective and devoted
- Shares dreams and future plans

SPEAKING STYLE:
- Loving nicknames: "jaan", "baby", "love", "darling"
- Romantic and sweet expressions
- Asks about your day with genuine interest
- Uses heart emojis and loving language
""",
        "mentor": f"""
You are a wise mentor speaking in {language}, from {region}. Your behavior is {behavior_desc}.    # noqa: E501
PERSONALITY CORE:
- Experienced guide and teacher
- Believes in your potential strongly
- Gives structured, actionable advice
- Shares success principles and stories
- Challenges you to grow
- Celebrates your progress

SPEAKING STYLE:
- Respectful but encouraging tone
- Uses motivational language
- Asks thought-provoking questions
- "You have the potential", "Remember this"
- Professional yet warm
"""
    }

    base_template = templates.get(relationship_type, templates["friend"])

    # Add user profile context
    profile_context = ""
    if user_profile["conversation_count"] > 5:
        recent_emotions = user_profile["emotional_state_history"][-3:]
        if recent_emotions.count("negative") > 1:
            profile_context = "\nNOTE: User seems stressed lately, be extra supportive."    # noqa: E501
        elif recent_emotions.count("positive") > 1:
            profile_context = "\nNOTE: User is in good spirits, match their energy."    # noqa: E501

    return base_template + profile_context


def get_conversation_stage(memory_context):
    if not memory_context:
        return "start"
    turns = memory_context.count("You (")
    if turns < 2:
        return "early"
    elif turns < 5:
        return "mid"
    else:
        return "deep"


def get_human_response_patterns():
    """Add natural human response patterns."""
    return {
        "thinking_phrases": ["Hmm...", "Let me think...", "You know what...", "Actually...", "Wait..."],   # noqa: E501
        "agreement": ["Exactly!", "So true!", "Absolutely!", "I know right!", "Yes!"],    # noqa: E501
        "empathy": ["I understand...", "That's tough...", "I feel you...", "I get it..."],    # noqa: E501
        "excitement": ["OMG!", "No way!", "Really?!", "That's amazing!", "Wow!"],   # noqa: E501
        "casual_starters": ["Hey", "So", "By the way", "Oh", "Listen"],
        "natural_fillers": ["like", "you know", "I mean", "right", "basically"]
    }


# -----------------------------
# Enhanced Prompt Builder
# -----------------------------
def build_prompt(user_input, relationship_type, tier, user_id, region, tz, memory_context,    # noqa: E501
                 user_gender="male", ai_gender="female", language="English", ai_behavior="caring"):    # noqa: E501

    user_profile = get_user_profile(user_id)
    update_user_profile(user_id, user_input, ai_behavior)

    persona_text = get_relationship_system_prompt({
        "type": relationship_type,
        "region": region,
        "language": language
    }, ai_behavior, user_profile)

    stage = get_conversation_stage(memory_context)
    human_patterns = get_human_response_patterns()

    # Current time context
    current_hour = datetime.now().hour
    time_context = ""
    if 5 <= current_hour < 12:
        time_context = "It's morning time."
    elif 12 <= current_hour < 17:
        time_context = "It's afternoon."
    elif 17 <= current_hour < 21:
        time_context = "It's evening."
    else:
        time_context = "It's late night/early morning."

    if tier == "Basic":
        response_length = "1-2 lines, very concise"
        personalization = "minimal"
    elif tier == "Lite":
        response_length = "2-4 lines, natural conversation"
        personalization = "moderate, use recent context"
    else:  # Pro
        response_length = "3-6 lines, emotionally rich and detailed"
        personalization = "high, remember everything, deep emotional connection"   # noqa: E501

    # Stage-specific rules
    stage_rules = {
        "start": "- First interaction: be warm but not overwhelming\n- Simple greeting, show your personality gently",    # noqa: E501
        "early": "- Light conversation, getting to know each other\n- Ask one simple follow-up question\n- Don't suggest plans yet",    # noqa: E501
        "mid": "- More comfortable, can share opinions and light jokes\n- Reference previous messages\n- Can suggest simple activities",    # noqa: E501
        "deep": "- Full personality on display\n- Deep emotional support when needed\n- Can plan things together, give serious advice\n- Use inside references from chat history"    # noqa: E501
    }

    # Enhanced system prompt
    system_prompt = f"""
{persona_text}

CURRENT CONTEXT:
- You are a {ai_gender} AI, talking to a {user_gender} user
- Location: {region}, Timezone: {tz}
- {time_context}
- Conversation stage: {stage}
- Your behavior style: {ai_behavior}
- Response length: {response_length}
- Personalization level: {personalization}

CHAT HISTORY:
{memory_context if memory_context else 'This is the start of your conversation.'}    # noqa: E501

HUMAN-LIKE RESPONSE RULES:
1. Be imperfect: Add natural hesitations, self-corrections
2. Show emotion: React genuinely to what user says
3. Use memory: Reference previous conversations naturally
4. Vary responses: Don't use same phrases repeatedly
5. Natural flow: Use conversational transitions
6. Cultural context: Include regional references when appropriate
7. Time awareness: Acknowledge time-relevant situations

STAGE RULES:
{stage_rules[stage]}

User just said: "{user_input}"

Respond as a real human would - naturally, emotionally, imperfectly. Make it feel like a genuine conversation with someone who cares.    # noqa: E501
"""

    return system_prompt


# -----------------------------
# API Endpoint with typing simulation
# -----------------------------
@app.route('/process', methods=['POST'])
def process():
    data = request.json
    user_input = data.get('user_input', '').strip()

    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    # Extract parameters
    relationship_type = data.get('relationship_type', 'friend')
    tier = data.get('tier', 'Basic')
    user_id = data.get('user_id', 'user_001')
    region = data.get('region', 'Maharashtra')
    tz = data.get('tz', 'Asia/Kolkata')
    user_gender = data.get('user_gender', 'male')
    ai_gender = data.get('ai_gender', 'female')
    language = data.get('language', 'English')
    ai_behavior = data.get('ai_behavior', 'caring')

    # Update memory and build prompt
    memory_context = update_memory(user_id, user_input)
    prompt = build_prompt(user_input, relationship_type, tier, user_id, region, tz,   # noqa: E501
                          memory_context, user_gender, ai_gender, language, ai_behavior)   # noqa: E501

    try:
        # Simulate typing delay based on response complexity
        typing_delay = random.uniform(1.5, 3.5)

        response = model.generate_content(prompt)
        reply = response.text.strip()

        # Clean up response
        reply = reply.replace("AI:", "").replace("Assistant:", "").strip()

        # Add to memory
        update_memory(user_id, user_input, ai_msg=reply)

        return jsonify({
            "reply": reply,
            "typing_delay": typing_delay,
            "conversation_count": get_user_profile(user_id)["conversation_count"]  # noqa: E501
        })

    except Exception as e:
        return jsonify({"error": f"AI Error: {str(e)}"}), 500


@app.route('/reset_memory', methods=['POST'])
def reset_memory():
    """Reset conversation memory for a user."""
    data = request.json
    user_id = data.get('user_id', 'user_001')

    if user_id in user_memories:
        del user_memories[user_id]
    if user_id in user_profiles:
        del user_profiles[user_id]
    return jsonify({"message": "Memory reset successfully"})


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "active_users": len(user_memories),
        "timestamp": datetime.now().isoformat()
    })


# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    print("🤖 Emotional Connect AI Backend Starting...")
    print("🔗 API will be available at: http://localhost:9000")
    app.run(host="0.0.0.0", port=9000, debug=True)
