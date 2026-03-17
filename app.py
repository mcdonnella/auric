from flask import Flask, request
import requests
import yaml

# Load configuration from config.yaml
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

# Pull credentials from config
TELEGRAM_TOKEN = config["telegram"]["bot_token"]
MONDAY_API_TOKEN = config["monday"]["api_token"]
MONDAY_BOARD_ID = config["monday"]["board_id"]

# Initialise Flask app
app = Flask(__name__)

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    
    # Extract the message text and chat ID from the incoming Telegram update
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    
    parsed = parse_message(text)
    
    if parsed is None:
        print("Message format not recognised")
        return "ok", 200
    
    print(f"Parent item: {parsed['parent_item']}")
    print(f"Sub-item: {parsed['sub_item']}")
    
    return "ok", 200

if __name__ == "__main__":
    app.run(port=5000)

def parse_message(text):
    # Get the prefix and separator from config
    prefix = config["message_format"]["prefix"]
    separator = config["message_format"]["separator"]
    
    # Check the message starts with the correct prefix e.g. "ADD"
    if not text.startswith(prefix):
        return None
    
    # Split the message by the separator e.g. "|"
    parts = text.split(separator)
    
    # We expect exactly 3 parts: ADD | Parent Item | Sub-item
    if len(parts) != 3:
        return None
    
    # Strip whitespace from each part and return as a dictionary
    return {
        "parent_item": parts[1].strip(),
        "sub_item": parts[2].strip()
    }