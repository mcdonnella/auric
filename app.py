from flask import Flask, request
import requests
import yaml
import urllib3
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load from environment variables if available (Railway), otherwise use config.yaml
if os.path.exists("config.yaml"):
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
    TELEGRAM_TOKEN = config["telegram"]["bot_token"]
    MONDAY_API_TOKEN = config["monday"]["api_token"]
    MONDAY_BOARD_ID = config["monday"]["board_id"]
else:
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    MONDAY_API_TOKEN = os.environ.get("MONDAY_API_TOKEN")
    MONDAY_BOARD_ID = os.environ.get("MONDAY_BOARD_ID")

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
    
    success, result = create_monday_subitem(parsed["parent_item"], parsed["sub_item"])
    
    if success:
        print(f"Sub-item created: {result}")
    else:
        print(f"Error: {result}")
    
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

def create_monday_subitem(parent_item_name, sub_item_name):
    # Monday.com API endpoint
    url = "https://api.monday.com/v2"
    
    # Headers to authenticate with Monday.com
    headers = {
        "Authorization": MONDAY_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    # First query - find the parent item ID by searching for its name on the board
    search_query = f"""
    query {{
        boards(ids: {MONDAY_BOARD_ID}) {{
            items_page {{
                items {{
                    id
                    name
                }}
            }}
        }}
    }}
    """
    
    # Send the search request to Monday.com
    response = requests.post(url, json={"query": search_query}, headers=headers, verify=False)
    data = response.json()
    
    # Loop through items to find matching parent item name
    items = data["data"]["boards"][0]["items_page"]["items"]
    parent_id = None
    for item in items:
        if item["name"].lower() == parent_item_name.lower():
            parent_id = item["id"]
            break
    
    # If no matching parent item found, return an error
    if not parent_id:
        return False, f"Could not find parent item: {parent_item_name}"
    
    # Second query - create the sub-item under the parent item
    create_query = f"""
    mutation {{
        create_subitem(parent_item_id: {parent_id}, item_name: "{sub_item_name}") {{
            id
            name
        }}
    }}
    """
    
    # Send the create request to Monday.com
    response = requests.post(url, json={"query": create_query}, headers=headers, verify=False)
    data = response.json()
    
    return True, sub_item_name