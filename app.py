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
    
    print(f"Received message: {text} from chat_id: {chat_id}")
    
    return "ok", 200

if __name__ == "__main__":
    app.run(port=5000)