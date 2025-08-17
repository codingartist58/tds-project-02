import base64
from io import BytesIO
import io
import json
import os
import google.generativeai as genai
from matplotlib import pyplot as plt
import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Gemini with API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))



def clean_json(parsed_response: str):
    """
    Clean Gemini output and return dict or list.
    """
    if isinstance(parsed_response, str):
        parsed_response = parsed_response.strip()
        if parsed_response.startswith("```"):
            parsed_response = parsed_response.strip("`")
            if parsed_response.startswith("json"):
                parsed_response = parsed_response[len("json"):].strip()
        try:
            return json.loads(parsed_response)
        except Exception as e:
            return {"error": f"Failed to parse JSON: {str(e)}", "raw": parsed_response}
    return parsed_response



import pandas as pd
import requests

# Fetch all HTML tables from a given URL.
def get_tables_from_url(url: str):
    """
    Fetch all HTML tables from a given URL.
    
    Args:
        url (str): The webpage URL containing tables.

    Returns:
        list[dict]: A list of tables where each table is represented as:
                    {
                        "table_index": int,
                        "data": list[dict]   # rows as dicts
                    }
    """
    try:
        # verify the URL is reachable
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Use pandas to parse tables
        tables = pd.read_html(response.text)

        results = []
        for idx, df in enumerate(tables):
            results.append({
                "table_index": idx,
                "data": df.to_dict(orient="records")
            })

        return results

    except ValueError:
        # No tables found
        return []
    except Exception as e:
        return {"error": str(e)}


def render_plots(json_response, data):

    # if json_response is a Dictionary
    if isinstance(json_response, dict):
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
                    json_response[key] = "failed: " + str(e)

        return json_response

    # if json_response is a list
    elif isinstance(json_response, list):
        for i in range(len(json_response)):
            item = json_response[i]
            if isinstance(item, dict):
                
                code = item["plot"]
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
                    json_response[i] = b64_img
                except Exception as e:
                    json_response[i] = "failed: " + str(e)

        return json_response

def process_questions(questions_text: str, context_data: dict) -> str:
    """Send the questions text to AIpipe and return its response."""
    
    

    #scrape URLs for context
    url_contents = []
    for url in context_data.get("urls", []):
        content = get_tables_from_url(url)
        url_contents.append(content)
    
    

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
- Tables from URL Contents: {url_contents}

QUESTIONS: {questions_text}

Answer the questions using the context data. Follow the exact format specified in the questions. If a chart/plot is requested, provide matplotlib code, under a 'plot' property."""
    
    try:
        model = genai.GenerativeModel("gemini-2.5-pro")

        # Call Gemini
        response = model.generate_content([
    {"role": "user", "parts": [system_prompt]},
    {"role": "user", "parts": [user_prompt]}])
        
        try:
            if response.candidates and response.candidates[0].content.parts:
                raw_text = response.candidates[0].content.parts[0].text.strip()
            else:
                raw_text = ""
        except Exception:
            raw_text = ""
        # raw_text = response.text.strip()
        print("--[DEBUG] Raw Gemini response: ", raw_text)

        #clean json
        parsed_response = clean_json(raw_text)

        parsed_response = render_plots(parsed_response, context_data)

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

    