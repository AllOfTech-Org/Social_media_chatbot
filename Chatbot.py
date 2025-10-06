import os
import json
import numpy as np
from transformers import AutoTokenizer, AutoModel
import logging
import requests
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

# ✅ Load environment variables
load_dotenv()

# ✅ Fix Hugging Face cache permissions (for Railway)
os.environ["HF_HOME"] = "./hf_cache"
os.environ["TRANSFORMERS_CACHE"] = "./hf_cache"

# ✅ Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Chatbot")

# ✅ Configuration
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = "deepseek/deepseek-chat-v3.1:free"

# ===============================
# 🔹 Lightweight Embedding System
# ===============================
class SimpleEmbeddingModel:
    def __init__(self, model_name=MODEL_NAME):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            embeddings = self.model(**inputs).last_hidden_state.mean(dim=1)
        return embeddings.cpu().numpy()

embeddings_model = SimpleEmbeddingModel()

# Example product data (replace with your actual knowledge base if needed)
PRODUCT_DATA = {
    "AllOfTech": [
        "AllOfTech is a technology agency specializing in AI/ML, blockchain, web and mobile app development.",
        "We provide UX/UI design, branding, and predictive analytics solutions.",
        "Our goal is to help startups and businesses scale with innovative AI-driven products."
    ]
}

# ===============================
# 🔹 Chat Logic
# ===============================
def search_similar_chunks(query, product="AllOfTech", k=2):
    """Find top-k most relevant sentences from product data."""
    if product not in PRODUCT_DATA:
        return []
    corpus = PRODUCT_DATA[product]
    query_emb = embeddings_model.encode(query)
    corpus_emb = embeddings_model.encode(corpus)
    similarities = cosine_similarity(query_emb, corpus_emb)[0]
    top_indices = np.argsort(similarities)[::-1][:k]
    return [corpus[i] for i in top_indices]


def generate_response(query, context, product="AllOfTech"):
    """Generate chatbot response using OpenRouter API."""
    if not context:
        return (
            "Welcome to AllOfTech! We specialize in AI/ML, blockchain, "
            "web and mobile app development, UX/UI design, and branding. "
            "How can we help you today?"
        )

    prompt = f"""Context:\n{chr(10).join(context)}\n\n
    You are the AI assistant for AllOfTech — a leading technology agency.
    Be clear, friendly, and professional when answering:
    "{query}"
    """

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            }),
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            logger.error(f"OpenRouter API error: {response.text}")
            return "Sorry, I faced an issue while generating your response."
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "System interruption detected. Please try again shortly."


def chatbot(message, product="AllOfTech"):
    """Main chatbot entry point."""
    context = search_similar_chunks(message, product)
    reply = generate_response(message, context, product)
    return reply
