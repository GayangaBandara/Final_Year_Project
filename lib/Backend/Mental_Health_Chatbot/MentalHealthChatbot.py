from fastapi import FastAPI
from pydantic import BaseModel
import json
import os
import random
import re
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
<<<<<<< HEAD:lib/Mental_Health_Chatbot/MentalHealthChatbot.py
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Access your key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Loaded from environment only. Do not hardcode secrets.
=======

# Set your API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
>>>>>>> 1c277e6f932727e1ad17911806f0edbae4dc697e:lib/Backend/Mental_Health_Chatbot/MentalHealthChatbot.py

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Load mental health dataset
try:
    with open("MentalHealthChatbotDataset.json", "r", encoding="utf-8") as file:
        dataset = json.load(file)
    print("✅ Dataset loaded successfully")
except Exception as e:
    print(f"❌ Error loading dataset: {e}")
    dataset = {}

# Rotating simple responses
SIMPLE_RESPONSES = {
    "hi": [
        "**HELLO!** How can I support you today?",
        "**HI THERE!** Hope your day is going okay.",
        "**HEY FRIEND!** How are you feeling right now?"
    ],
    "hello": [
        "**HI THERE!** I'm here to listen.",
        "**HELLO!** Glad you reached out today.",
        "**HEY!** How are things going for you?"
    ],
    "hey": [
        "**HEY!** How are you feeling?",
        "**HI!** I'm here for you.",
        "**HEY FRIEND!** Want to share what’s on your mind?"
    ],
    "bye": [
        "**TAKE CARE!** Remember you're not alone.",
        "**GOODBYE!** Wishing you peace and comfort.",
        "**BYE FOR NOW!** Reach out anytime."
    ],
    "goodbye": [
        "**BE WELL!** Reach out anytime.",
        "**GOODBYE!** You're stronger than you think.",
        "**SEE YOU SOON!** Take good care of yourself."
    ],
    "thanks": [
        "**YOU'RE WELCOME!** I'm here if you need more support.",
        "**ANYTIME!** I'm glad to be here for you.",
        "**OF COURSE!** You're not alone in this."
    ]
}

# Available Groq models
MODELS = {
    "Llama3-70B": "llama3-70b-8192",
    "Mixtral-8x7B": "mixtral-8x7b-32768"
}

# Crisis-related keywords
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life",
    "can't go on", "self harm", "hurt myself"
]

def contains_crisis(message: str) -> bool:
    return any(kw in message.lower() for kw in CRISIS_KEYWORDS)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    model: str = "Llama3-70B"  # Default to Llama 3 70B

class ChatResponse(BaseModel):
    response: str

def clean_response(text: str, crisis_mode: bool = False) -> str:
    """Clean the AI response and enforce hotline rules"""
    # Remove any system prompt remnants
    text = text.split("AI:")[-1].strip()

    # Ensure first sentence is uppercase encouraging
    if "\n" in text:
        first_line, rest = text.split("\n", 1)
        first_line = first_line.upper()
        text = f"{first_line}\n{rest}"
    else:
        sentences = text.split(".")
        if len(sentences) > 1:
            first_sentence = sentences[0].strip().upper()
            rest = ". ".join(sentences[1:]).strip()
            text = f"{first_sentence}. {rest}"

    # Remove quotation marks
    text = text.replace('"', '').replace("'", "")

    # Remove hotline numbers if NOT crisis mode
    if not crisis_mode:
        text = re.sub(r"(Sumithrayo.*?\d+|Psychiatrists.*?\d+|Helpline.*?\d+)", "", text, flags=re.IGNORECASE)

    # Ensure ends with positive note
    positive_phrases = ["remember", "you can", "try", "hope", "suggestion"]
    if not any(phrase in text.lower() for phrase in positive_phrases):
        text += " Remember, small steps can make a big difference."

    return text.strip()

def query_groq(model: str, prompt: str, max_tokens: int = 512) -> str:
    """Query Groq's API"""
    response = groq_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a compassionate mental health assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.7
    )
    return response.choices[0].message.content

@app.post("/chat", response_model=ChatResponse)
def chat_with_bot(request: ChatRequest):
    user_message = request.message.lower().strip()

    # Simple responses
    if user_message in SIMPLE_RESPONSES:
        return ChatResponse(response=random.choice(SIMPLE_RESPONSES[user_message]))

    # Crisis detection
    crisis_mode = contains_crisis(user_message)
    if crisis_mode:
        crisis_response = (
            "**I'M REALLY CONCERNED ABOUT YOU.** You are not alone in this, and help is available.\n"
            "👉 You can call **Sumithrayo Hotline (011 2 682 682)** or "
            "**Sri Lanka College of Psychiatrists Helpline (071 722 5222)** right now for immediate support.\n"
            "Please reach out—you deserve help and care."
        )
        return ChatResponse(response=crisis_response)

    # Add context from dataset
    context = ""
    for keyword, advice in dataset.items():
        if keyword.lower() in user_message:
            context = f"\nRelevant information: {advice}"
            break

    # Prompt engineering
    prompt = f"""Respond to this message:
    "{request.message}"{context}

    Response requirements:
    - Start with one encouraging sentence
    - Use a warm, friendly tone
    - Avoid medical jargon or robotic wording
    - Give practical, everyday suggestions
    - Share hotline numbers ONLY if user expresses suicidal thoughts or self-harm
    - Do not use Sinhala
    - End with a hopeful or empowering note
    """

    try:
        if request.model not in MODELS:
            return ChatResponse(response=f"Error: Model {request.model} not found")

        response = query_groq(MODELS[request.model], prompt)
        cleaned_response = clean_response(response, crisis_mode=crisis_mode)
        return ChatResponse(response=cleaned_response)

    except Exception as e:
        print(f"Error generating response: {e}")
        return ChatResponse(response="**I'M HERE FOR YOU.** Let's try that again. Could you rephrase your message?")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
