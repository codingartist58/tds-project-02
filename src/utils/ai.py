import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
AIPIPE_BASE_URL = os.getenv("AIPIPE_BASE_URL")

if not AIPIPE_TOKEN or not AIPIPE_BASE_URL:
    raise ValueError("Missing AIPIPE_TOKEN or AIPIPE_BASE_URL in environment variables")

def process_questions(questions_text: str) -> str:
    """Send the questions text to AIpipe and return its response."""
    
    url = f"{AIPIPE_BASE_URL.rstrip('/')}/completions"

    headers = {
        "Authorization": f"Bearer {AIPIPE_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-3.5-turbo-instruct",  # completions model
        "prompt": f"You are a helpful data analyst. Answer these questions:\n\n{questions_text}",
        "max_tokens": 500,
        "temperature": 0
    }

    print(f"[DEBUG] Sending request to: {url}")

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"AIpipe API error {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["text"].strip()
