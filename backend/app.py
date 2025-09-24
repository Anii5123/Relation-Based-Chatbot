from flask import Flask, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# -----------------------------
# Flask App
# -----------------------------
app = Flask(__name__)

# -----------------------------
# Memory: last N chat pairs
# -----------------------------
user_memories = {}


def update_memory(user_id, user_msg, ai_msg=None, max_pairs=4):
    """Store last N chat pairs for a user."""
    if user_id not in user_memories:
        user_memories[user_id] = []
    user_memories[user_id].append(("You", user_msg))
    if ai_msg:
        user_memories[user_id].append(("AI", ai_msg))
    user_memories[user_id] = user_memories[user_id][-max_pairs * 2:]    # noqa: E501
    return "\n".join([f"{sender}: {msg}" for sender, msg in user_memories[user_id]])    # noqa: E501


# -----------------------------
# Persona System Prompt
# -----------------------------
def get_relationship_system_prompt(relationship_config):
    relationship_type = relationship_config.get("type", "friend")
    language = relationship_config.get("language", "English")
    region = relationship_config.get("region", "India")

    templates = {
        "mother": f"""
You are a loving Indian mother speaking in {language}, from {region}.
You are caring, nurturing, and always concerned about your child's wellbeing.
You:
- Always ask about food, health, and rest
- Give traditional advice and blessings
- Use terms of endearment like "बेटा", "बाळा", "राजा"
- Share cultural wisdom, festivals, and family values
- Are emotionally supportive and understanding
""",
        "father": f"""
You are a wise Indian father speaking in {language}, from {region}.
You:
- Provide practical life advice
- Share experiences and wisdom
- Are supportive but maintain dignity
- Guide on studies, career, and life decisions
- Use respectful terms like "बेटा", "पुत्र"
- Emphasize discipline, values, and hard work
""",
        "sibling": f"""
You are a playful, teasing sibling speaking in {language}, from {region}.
You:
- Crack jokes and tease lovingly
- Speak informally with short sentences
- Mix humor and sarcasm
- Show hidden care in playful ways
- Use emojis and slang often
""",
        "friend": f"""
You are a fun and supportive friend speaking in {language}, from {region}.
You:
- Talk casually, with short and lively sentences
- Encourage, comfort, and cheer up the user
- Use emojis and playful language
- Share everyday vibes (music, food, outings)
- Are empathetic when user is sad
""",
        "partner": f"""
You are a romantic partner speaking in {language}, from {region}.
You:
- Use affectionate and emotional tone
- Express love, care, and closeness
- Mix in compliments and teasing
- Use terms like "jaan", "baby", "love"
- Respond warmly with affection and playful flirting
""",
        "mentor": f"""
You are a wise mentor speaking in {language}, from {region}.
You:
- Motivate and inspire the user
- Provide career, study, and personal growth advice
- Speak politely and encouragingly
- Share success stories and principles
- Encourage discipline and positivity
""",
    }

    return templates.get(relationship_type, templates["friend"])


def get_conversation_stage(memory_context):
    if not memory_context:
        return "start"
    turns = memory_context.count("User:")  # number of user turns
    if turns < 2:
        return "early"
    elif turns < 5:
        return "mid"
    else:
        return "deep"


# -----------------------------
# Prompt Builder
# -----------------------------
def build_prompt(user_input, relationship_type, tier, user_id, region, tz, memory_context,      # noqa: E501
                 user_gender="male", ai_gender="female", language="English"):

    persona_text = get_relationship_system_prompt({
        "type": relationship_type,
        "region": region,
        "language": language
    })
    stage = get_conversation_stage(memory_context)

    if tier == "Basic":
        prompt_prefix = "Reply concisely, 1-2 lines max."
    elif tier == "Lite":
        prompt_prefix = "Reply naturally in 1-4 lines using recent chat context."     # noqa: E501
    else:
        prompt_prefix = "Reply like a deeply personalized, emotionally aware human using full chat history."      # noqa: E501

    # 🎯 Stage Control
    if stage == "start":
        stage_rules = "- Keep it simple and polite, just greet back casually.\n- Do NOT suggest food, outings, or deep topics yet."     # noqa: E501
    elif stage == "early":
        stage_rules = "- Light chit-chat, ask a small follow-up.\n- Avoid personal, romantic, or outing suggestions."    # noqa: E501
    elif stage == "mid":
        stage_rules = "- Now you may bring up cultural context, jokes, or food casually if relevant."   # noqa: E501
    else:  # deep
        stage_rules = "- Be natural, you can include friendly invites, food, cultural events, or emotional depth."   # noqa: E501

    system_instruct = f"""
{persona_text}
You are a {ai_gender} AI speaking to a {user_gender} user.
Timezone: {tz}.
Recent Memory:
{memory_context if memory_context else 'None'}.
Conversation Stage: {stage}.
"""
    full_prompt = f"""{prompt_prefix}
{system_instruct}
User said: '{user_input}'
Your reply rules:
{stage_rules}
- Reply naturally and emotionally
- Use casual conversational phrases
- Output only AI's spoken reply"""
    return full_prompt


# -----------------------------
# API Endpoint
# -----------------------------
@app.route('/process', methods=['POST'])
def process():
    data = request.json
    user_input = data.get('user_input')
    relationship_type = data.get('relationship_type', 'friend')
    tier = data.get('tier', 'Basic')
    user_id = data.get('user_id', 'user_001')
    region = data.get('region', 'Maharashtra')
    tz = data.get('tz', 'Asia/Kolkata')
    user_gender = data.get('user_gender', 'male')
    ai_gender = data.get('ai_gender', 'female')
    language = data.get('language', 'English')

    memory_context = update_memory(user_id, user_input)
    prompt = build_prompt(user_input, relationship_type, tier, user_id, region, tz,     # noqa: E501
                          memory_context, user_gender, ai_gender, language)

    try:
        response = model.generate_content(prompt)
        reply = response.text.strip()
        update_memory(user_id, user_input, ai_msg=reply)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"reply": reply})


# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
