import os
import pickle
import faiss
import json
from sentence_transformers import SentenceTransformer
import logging
import requests
from dotenv import load_dotenv

# ✅ Hugging Face cache fix (Spaces cannot write to '/.cache')
os.environ["HF_HOME"] = "./hf_cache"
os.environ["TRANSFORMERS_CACHE"] = "./hf_cache"
os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./hf_cache"

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
PROCESSED_DATA_DIR = "processed_data"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "deepseek/deepseek-chat-v3.1:free"

# ✅ Initialize SentenceTransformer safely
try:
    embeddings_model = SentenceTransformer(MODEL_NAME, cache_folder="./hf_cache")
except Exception as e:
    logger.warning(f"Could not load '{MODEL_NAME}', using fallback model.")
    embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")

class ProductData:
    def __init__(self, product_name: str):
        self.product_name = product_name
        self.data_dir = os.path.join(PROCESSED_DATA_DIR, product_name)
        self.faiss_index = None
        self.chunks = None
        self.embeddings = None
        self.load_data()

    def load_data(self):
        try:
            faiss_path = os.path.join(self.data_dir, "faiss_store", "index.faiss")
            if os.path.exists(faiss_path):
                self.faiss_index = faiss.read_index(faiss_path)
            chunks_path = os.path.join(self.data_dir, "chunks.pkl")
            if os.path.exists(chunks_path):
                with open(chunks_path, "rb") as f:
                    data = pickle.load(f)
                    self.chunks = data["chunks"]
                    self.embeddings = data["embeddings"]
        except Exception as e:
            logger.error(f"Error loading data for {self.product_name}: {str(e)}")

class SimpleChatManager:
    def __init__(self):
        self.product_data = {}
        self.initialize_products()

    def initialize_products(self):
        try:
            if os.path.exists(PROCESSED_DATA_DIR):
                for product_name in os.listdir(PROCESSED_DATA_DIR):
                    product_path = os.path.join(PROCESSED_DATA_DIR, product_name)
                    if os.path.isdir(product_path):
                        self.product_data[product_name] = ProductData(product_name)
                        logger.info(f"Initialized data for product: {product_name}")
        except Exception as e:
            logger.error(f"Error initializing products: {str(e)}")
            raise

    def search_similar_chunks(self, query: str, product: str, k: int = 3) -> list:
        if product not in self.product_data:
            logger.warning(f"Product {product} not found in product data")
            return []
        product_data = self.product_data[product]
        if not product_data.faiss_index or not product_data.chunks:
            logger.warning(f"No FAISS index or chunks found for product {product}")
            return []
        try:
            query_embedding = embeddings_model.encode([query])[0]
            distances, indices = product_data.faiss_index.search(
                query_embedding.reshape(1, -1).astype("float32"), k
            )
            relevant_chunks = []
            for idx in indices[0]:
                if idx < len(product_data.chunks):
                    chunk = product_data.chunks[idx]
                    relevant_chunks.append(f"[{product.upper()}] {chunk}")
            return relevant_chunks
        except Exception as e:
            logger.error(f"Error searching chunks for product {product}: {str(e)}")
            return []

    def generate_response(self, query: str, context: list, product: str) -> str:
        if not context:
            return (
                "Welcome to AllOfTech! We're a technology agency specializing in AI/ML, "
                "blockchain, web and mobile apps, UX/UI design, and branding. "
                "How can we help you achieve your goals?"
            )

        prompt = f"""Context:\n{chr(10).join(context)}\n\nInstructions:\n
        You are the voice of AllOfTech, a cutting-edge technology agency dedicated to delivering innovative solutions in AI/ML, blockchain, web development, mobile apps, UX/UI design, and graphics & branding.

        Respond to: "{query}"
        """

        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
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
                return "Sorry, I faced an issue while generating the response."
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "System interruption detected. Please try again shortly."

# ✅ Initialize the chatbot manager
simple_chat_manager = SimpleChatManager()

def chatbot(message: str, product: str = "AllOfTech") -> str:
    relevant_chunks = simple_chat_manager.search_similar_chunks(message, product)
    response = simple_chat_manager.generate_response(message, relevant_chunks, product)
    return response
