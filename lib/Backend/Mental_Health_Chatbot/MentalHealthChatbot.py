from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
import os
import json
import random
import re
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Load environment variables
# -------------------------------------------------------------------
load_dotenv()

# -------------------------------------------------------------------
# Available Groq models (include compatibility alias)
# -------------------------------------------------------------------
MODELS = {
    "default": "llama3-70b-8192",
    "Llama3-70B": "llama3-70b-8192",
    "Mixtral-8x7B": "mixtral-8x7b-32768",
    "llama2-70b-4096": "llama3-70b-8192"  # alias for frontend compatibility
}

# -------------------------------------------------------------------
# Initialize router and Groq client
# -------------------------------------------------------------------
router = APIRouter()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

print(f"✅ Found GROQ_API_KEY: {'*' * len(GROQ_API_KEY[:4])}...{'*' * len(GROQ_API_KEY[-4:])}")

try:
    groq_client = Groq(api_key=GROQ_API_KEY)
    # Test connection with default model
    test_response = groq_client.chat.completions.create(
        model=MODELS["default"],
        messages=[{"role": "user", "content": "test"}],
        max_tokens=10
    )
    print("✅ Successfully connected to Groq API")
except Exception as e:
    print(f"❌ Error connecting to Groq API: {str(e)}")

# -------------------------------------------------------------------
# Crisis-related keywords and response
# -------------------------------------------------------------------
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life",
    "can't go on", "self harm", "hurt myself"
]

# Crisis response (updated as per your rules)
CRISIS_RESPONSE = (
    "I'm really concerned about you. You don’t have to go through this alone—"
    "sometimes sharing what you feel can lighten the weight a little. "
    "It may help to do something simple like reaching out to a trusted friend or stepping outside for fresh air.\n\n"
    "If you’re thinking about suicide or self-harm, please call **Sumithrayo Hotline (011 2 682 682)** "
    "or **Sri Lanka College of Psychiatrists Helpline (071 722 5222)** for immediate support.\n\n"
    "You are stronger than you think, and better days can still come."
)

# -------------------------------------------------------------------
# Load mental health dataset
# -------------------------------------------------------------------
try:
    dataset_path = os.path.join(os.path.dirname(__file__), "MentalHealthChatbotDataset.json")
    with open(dataset_path, "r", encoding="utf-8") as file:
        raw_dataset = json.load(file)
        dataset = {}
        for intent in raw_dataset.get("intents", []):
            if "tag" in intent and "responses" in intent:
                dataset[intent["tag"]] = intent["responses"][0]
    print("✅ Dataset loaded successfully")
except Exception as e:
    print(f"❌ Error loading dataset: {e}")
    dataset = {}

# -------------------------------------------------------------------
# Simple rotating responses
# -------------------------------------------------------------------
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

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def contains_crisis(message: str) -> bool:
    return any(kw in message.lower() for kw in CRISIS_KEYWORDS)

def clean_response(text: str, crisis_mode: bool = False) -> str:
    """Clean the AI response and enforce hotline rules"""
    text = text.split("AI:")[-1].strip()

    # Uppercase first line
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

    text = text.replace('"', '').replace("'", "")

    # Remove hotline numbers if not crisis mode
    if not crisis_mode:
        text = re.sub(r"(Sumithrayo.*?\d+|Psychiatrists.*?\d+|Helpline.*?\d+)", "", text, flags=re.IGNORECASE)

    # Ensure positive ending
    positive_phrases = ["remember", "you can", "try", "hope", "suggestion"]
    if not any(phrase in text.lower() for phrase in positive_phrases):
        text += " Remember, small steps can make a big difference."

    return text.strip()

def query_groq(model: str, prompt: str, max_tokens: int = 512) -> str:
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

# -------------------------------------------------------------------
# Pydantic Models
# -------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    model: str = "default"

class ChatResponse(BaseModel):
    response: str

# -------------------------------------------------------------------
# Chat Endpoint
# -------------------------------------------------------------------
@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    try:
        user_message = request.message.lower().strip()

        # Simple responses
        if user_message in SIMPLE_RESPONSES:
            return ChatResponse(response=random.choice(SIMPLE_RESPONSES[user_message]))

        # Crisis check FIRST (before model validation)
        crisis_mode = contains_crisis(user_message)
        if crisis_mode:
            return ChatResponse(response=CRISIS_RESPONSE)

        # Add context from dataset
        context = ""
        for keyword, advice in dataset.items():
            if keyword.lower() in user_message:
                context = f"\nRelevant information: {advice}"
                break

        # Prompt
        prompt = f"""As a mental health support assistant, respond with empathy and care:

        User's message: "{request.message}"
        {context}

        Response requirements:
            - Start with one encouraging sentence
            - Use a warm, friendly tone
            - Avoid medical jargon or robotic wording
            - Give practical, everyday suggestions
            - Share hotline numbers ONLY if user expresses suicidal thoughts or self-harm
            - Do not use Sinhala
            - End with a hopeful or empowering note
            - Maintain hope and encouragement
        """

        # Model validation
        if request.model not in MODELS:
            available = ", ".join(MODELS.keys())
            return ChatResponse(
                response=f"I apologize, but the model '{request.model}' is not available. Available models are: {available}"
            )

        try:
            completion = groq_client.chat.completions.create(
                model=MODELS[request.model],
                messages=[
                    {
                        "role": "system",
                        "content": "You are SafeSpace Assistant, a supportive mental health chatbot focused on providing emotional support and encouragement."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300,
                top_p=1,
                stream=False
            )

            response_text = completion.choices[0].message.content
            return ChatResponse(response=clean_response(response_text, crisis_mode=crisis_mode))

        except Exception as e:
            print(f"Groq API Error - {type(e).__name__}: {str(e)}")
            if "not found" in str(e).lower():
                return ChatResponse(response="I'm having trouble with the selected model. Please try another.")
            elif "timeout" in str(e).lower():
                return ChatResponse(response="The request timed out. Please try again in a moment.")
            elif "rate limit" in str(e).lower():
                return ChatResponse(response="Too many requests right now. Please wait and try again.")
            else:
                return ChatResponse(response="I'm having trouble connecting to my language model right now. Please try again later.")

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return ChatResponse(response="I'm sorry, something went wrong. Please try again in a moment.")

# -------------------------------------------------------------------
# End of file
# -------------------------------------------------------------------
