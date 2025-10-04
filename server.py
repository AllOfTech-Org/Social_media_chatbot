from flask import Flask, request
import requests
import os
from dotenv import load_dotenv
from Chatbot import chatbot   # Import your RAG chatbot function

# Load environment variables
load_dotenv()

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# ✅ Verify webhook
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    token_sent = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token_sent == os.getenv("VERIFY_TOKEN"):
        return challenge
    return "Invalid verification token", 403



# 📩 Handle incoming messages
@app.route("/webhook", methods=["POST"])
def handle_message():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                if "message" in event and "text" in event["message"]:
                    user_message = event["message"]["text"]
                    bot_reply = chatbot(user_message)  # 👈 Calls your RAG bot
                    send_message(sender_id, bot_reply)
    return "OK", 200


# ✉️ Send message back to user
def send_message(recipient_id, text):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Render's port if available, fallback to 5000 locally
    app.run(host="0.0.0.0", port=port, debug=True)
