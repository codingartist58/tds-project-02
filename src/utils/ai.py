import base64
from io import BytesIO
import io
import json
import os
import matplotlib
from matplotlib import pyplot as plt
import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
AIPIPE_BASE_URL = os.getenv("AIPIPE_BASE_URL")

if not AIPIPE_TOKEN or not AIPIPE_BASE_URL:
    raise ValueError("Missing AIPIPE_TOKEN or AIPIPE_BASE_URL in environment variables")

def clean_json(parsed_response):
    
    return parsed_response

def render_plots(json_response, data):
    for key, value in json_response.items():
        if isinstance(value, dict) and "plot" in value:
            code = value["plot"]
            try:
                # Execute code in safe environment
                local_env = {"df": data.copy(), "plt": plt}
                exec(code, {}, local_env)
                
                # Convert to base64
                buf = io.BytesIO()
                plt.savefig(buf, format="png")
                buf.seek(0)
                b64_img = base64.b64encode(buf.read()).decode("utf-8")
                plt.close()
            
            # Replace the plot code with base64 image
                json_response[key] = b64_img
            except Exception as e:
                value["plot_status"] = "failed"
                value["plot_error"] = str(e)    
    return json_response

def process_questions(questions_text: str, context_data: dict, model_choice: str = "gpt-4.1") -> str:
    """Send the questions text to AIpipe and return its response."""
    
    url = f"{AIPIPE_BASE_URL.rstrip('/')}/completions"

    headers = {
        "Authorization": f"Bearer {AIPIPE_TOKEN}",
        "Content-Type": "application/json"
    }

    
    # model configuration
    model_configs = {
        "gpt-4.1": {
            "model": "gpt-4.1",
            "max_tokens": 4000,
            "temperature": 0,
            "use_chat": True
        },
        "o4-mini": {
            "model": "o4-mini", 
            "max_tokens": 4000,
            "temperature": 0,
            "use_chat": True
        },
        "gpt-4o": {
            "model": "gpt-4o",
            "max_tokens": 4000,
            "temperature": 0,
            "use_chat": True
        },
        "gpt-3.5-turbo": {  # Fallback option
            "model": "gpt-3.5-turbo",
            "max_tokens": 4000,
            "temperature": 0,
            "use_chat": True
        },
        "gpt-3.5-turbo-instruct": {  # Your current model (legacy)
            "model": "gpt-3.5-turbo-instruct",
            "max_tokens": 3500,
            "temperature": 0,
            "use_chat": False
        }
    }

    config = model_configs.get(model_choice, model_configs["gpt-4.1"])

    # Streamlined system prompt focused on following user's format
    system_prompt = """You are a data analyst AI. Your task is to: 
1. Answer the user's questions present in {questions_text} using all available data sources.
2. The {questions_text} has two sections: 
   - The response format (usually JSON with specific keys).
   - The actual questions. 
   Always follow the response format exactly.
3. If a chart/plot is requested:
   - Do NOT insert base64 image strings.
   - Instead, provide matplotlib code under a 'plot' property for the corresponding key.
     Example:
       "bar_chart": {
         "plot": "import matplotlib.pyplot as plt\\nplt.bar([...])"
       }
   - Leave the rest of the key unfilled; it will be filled later after the plot is generated.
4. Only generate matplotlib code if plotting is specifically requested.
5. Do not show detailed calculations unless explicitly asked.
6. Be concise and direct in your answers.
7. Never hallucinate data - use only what's provided.

IMPORTANT: Always return answers in the exact format requested in {questions_text}."""



    user_prompt = f"""
CONTEXT DATA:
- URLs: {context_data.get("urls", {})}
- CSV: {context_data.get("csvdata", [])}
- Images: {context_data.get("images_text", [])}
- PDFs: {context_data.get("pdfdata", [])}
- Text: {context_data.get("text", [])}

QUESTIONS: {questions_text}

Answer the questions using the context data. Follow the exact format specified in the questions. If a chart/plot is requested, provide matplotlib code, under a 'plot' property."""
    

    # Prepare payload based on model type
    if config["use_chat"]:
        # Chat completion format (for newer models)
        payload = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": config["max_tokens"],
            "temperature": config["temperature"]
        }
        endpoint = "chat/completions"
    else:
        # Legacy completion format
        payload = {
            "model": config["model"],
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "max_tokens": config["max_tokens"],
            "temperature": config["temperature"]
        }
        endpoint = "completions"


    # Update URL for chat completions
    if config["use_chat"]:
        url = f"{AIPIPE_BASE_URL.rstrip('/')}/chat/completions"
    
    print(f"[DEBUG] Using model: {config['model']}")
    print(f"[DEBUG] Endpoint: {url}")    
   

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract response based on format
        if config["use_chat"]:
            ai_response = data["choices"][0]["message"]["content"].strip()
        else:
            ai_response = data["choices"][0]["text"].strip()
        
        # Parse JSON response
        try:
            parsed_response = json.loads(ai_response)
        except json.JSONDecodeError:
            # Handle non-JSON responses gracefully
            parsed_response = {
                "answer": ai_response,
                "status": "json_parse_error",
                "raw_response": ai_response
            }
        
        # Clean the json response
        parsed_response = clean_json(parsed_response)

        parsed_response = render_plots(parsed_response, context_data)
        # Convert to JSON string for consistency

        # add model info globally
        #parsed_response["model_used"] = config["model"]

        return parsed_response

        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "status": "request_error"
        }
    except Exception as e:
        return {
            "error": f"Processing failed: {str(e)}",
            "status": "processing_error"
        }

    