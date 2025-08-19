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
from src.utils.logger import write_log
import networkx
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
    # url_contents = []
    # for url in context_data.get("urls", []):
    #     content = get_tables_from_url(url)
    #     url_contents.append(content)
    
    

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

CONTEXT DATA:
- URLs: {context_data.get("urls", {})}
- CSV: {context_data.get("csvdata", [])}
- Images: {context_data.get("images_text", [])}
- PDFs: {context_data.get("pdfdata", [])}
- Text: {context_data.get("text", [])}

QUESTIONS: {questions_text}

Answer the questions using the context data. Follow the exact format specified in the questions.

"""



    user_prompt = f"""
CONTEXT DATA:
- URLs: {context_data.get("urls", {})}
- CSV: {context_data.get("csvdata", [])}
- Images: {context_data.get("images_text", [])}
- PDFs: {context_data.get("pdfdata", [])}
- Text: {context_data.get("text", [])}

QUESTIONS: {questions_text}

Answer the questions using the context data. Follow the exact format specified in the questions."""
    
    models_to_try = ["gemini-2.5-pro", "gemini-2.5-flash"]

    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)

            # Call Gemini
            response = model.generate_content(system_prompt+user_prompt)
            """ response = model.generate_content([
        {"role": "user", "parts": [system_prompt]},
        {"role": "user", "parts": [user_prompt]}]) """

            write_log(f"Gemini model {model_name} response  before processing: {response}")

            raw_text = None
            if response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, "finish_reason", None)

                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    parts = candidate.content.parts
                    if parts:
                        raw_text = parts[0].text.strip()

                if not raw_text:
                    write_log(f"--[DEBUG] {model_name} returned no usable text. finish_reason={finish_reason}")

            if raw_text:
                write_log(f"--[DEBUG] Raw Gemini ({model_name}) response: {raw_text}")
                # clean JSON
                parsed_response = clean_json(raw_text)
                parsed_response = render_plots(parsed_response, context_data)
                return parsed_response

        except Exception as e:
            write_log(f"--[DEBUG] {model_name} failed with error: {str(e)}")
            continue  # try next model

    # If everything failed
    return {
        "error": "Gemini returned no usable response from any model",
        "status": "processing_error"
    }


    