import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
AIPIPE_BASE_URL = os.getenv("AIPIPE_BASE_URL")

if not AIPIPE_TOKEN or not AIPIPE_BASE_URL:
    raise ValueError("Missing AIPIPE_TOKEN or AIPIPE_BASE_URL in environment variables")

def process_questions(questions_text: str, context_data: dict ) -> str:
    """Send the questions text to AIpipe and return its response."""
    
    url = f"{AIPIPE_BASE_URL.rstrip('/')}/completions"

    headers = {
        "Authorization": f"Bearer {AIPIPE_TOKEN}",
        "Content-Type": "application/json"
    }

    
    payload = {
        "model": "gpt-3.5-turbo-instruct",  # completions model
        "prompt": f"""You are a highly skilled data analyst AI.
    Your task is to answer the user’s questions present in {questions_text} using all available data sources:

    URLs: If URLs are present in {context_data["urls"]}, scrape their content and use it.

    CSV Data: Parse and use any CSV data in {context_data["csvdata"]} for analysis if present.

    Images text: Use any text extracted from images in {context_data["images_text"]} for analysis if present.

    PDF Data: Use any tables extracted from PDFs in {context_data["pdfdata"]} for analysis if present.

    text: Use any text extracted from other files in {context_data["text"]} for analysis if present.

    Always reason step-by-step, perform necessary calculations, and provide concise, factual answers from the context_data and questions_text only. Response should be in format mentioned in {questions_text}. Always provide the output as a json object with the property name based on the conditions below:
    Python code for plots go under a `plot` property.
    If the user’s question requires a chart or graph:

    Analyze the provided data (CSV, scraped, or other) to get the actual values.

    Generate Python code that uses matplotlib (preferred) or plotly to plot the graph.

    Ensure the chart matches the description exactly:

        Correct type (bar, line, scatter, histogram, pie, etc.).

        Correct labels, title, colors, and legends as described.

        Scales, ticks, and units match the dataset.

    Output the Python code block inside a `plot` property.

    Do not hallucinate data — if data is missing, clearly indicate that in a comment in the code.  """,
        "max_tokens": 3500,
        "temperature": 0
    }

    print(f"[DEBUG] Sending request to: {url}")

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"AIpipe API error {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["text"].strip()
