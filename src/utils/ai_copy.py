import os
import json
import base64
import requests
from dotenv import load_dotenv
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

load_dotenv()
AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
AIPIPE_BASE_URL = os.getenv("AIPIPE_BASE_URL")

def process_questions_updated(questions_text: str, context_data: dict, model_choice: str = "gpt-4.1") -> dict:
    """
    Updated function with better model options and chat format.
    
    Args:
        questions_text: User's questions
        context_data: All extracted data
        model_choice: Choose from 'gpt-4.1', 'o4-mini', 'gpt-4o', or 'gpt-3.5-turbo' (fallback)
    """
    
    # Scrape URLs if present (your existing logic)
    if context_data.get("urls") and isinstance(context_data["urls"], list):
        scraped_data = scrape_multiple_urls(context_data["urls"])
        context_data["scraped_content"] = scraped_data
    
    # Model configuration
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
1. Answer user questions using ONLY the provided context data
2. Follow the EXACT response format specified in the user's questions
3. Generate matplotlib code ONLY if plotting is specifically requested in the questions
4. Do not show detailed calculations unless explicitly asked
5. Be concise and direct in your answers
6. Never hallucinate data - use only what's provided

IMPORTANT: The user's questions will specify the exact format they want. Follow it precisely."""

    user_prompt = f"""
CONTEXT DATA:
- URLs: {context_data.get("scraped_content", {})}
- CSV: {context_data.get("csvdata", [])}
- Images: {context_data.get("images_text", [])}
- PDFs: {context_data.get("pdfdata", [])}
- Text: {context_data.get("text", [])}

QUESTIONS: {questions_text}

Answer the questions using the context data. Follow the exact format specified in the questions. If a chart/plot is requested, provide matplotlib code under a 'plot' property."""

    url = f"{AIPIPE_BASE_URL.rstrip('/')}/completions"
    headers = {
        "Authorization": f"Bearer {AIPIPE_TOKEN}",
        "Content-Type": "application/json"
    }
    
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
        
        # Execute plot code if present
        if "plot" in parsed_response and parsed_response["plot"]:
            plot_result = execute_plot_code_safely(parsed_response["plot"], context_data)
            
            if plot_result and not plot_result.startswith("Error"):
                parsed_response["plot_image"] = plot_result
                parsed_response["plot_status"] = "success"
            else:
                parsed_response["plot_status"] = "failed"
                parsed_response["plot_error"] = plot_result
        
        parsed_response["model_used"] = config["model"]
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

def execute_plot_code_safely(code: str, context_data: dict) -> str:
    """Execute plot code and return base64 image (your existing function)."""
    try:
        # Your existing implementation
        safe_globals = {
            '__builtins__': {},
            'matplotlib': matplotlib,
            'plt': plt,
            'pd': pd,
            'pandas': pd,
            'json': json,
            'context_data': context_data
        }
        
        # Add CSV data as DataFrames
        if context_data.get('csvdata'):
            for i, csv_content in enumerate(context_data['csvdata']):
                try:
                    df = pd.read_csv(BytesIO(csv_content.encode()))
                    safe_globals[f'df{i}' if i > 0 else 'df'] = df
                except:
                    pass
        
        exec(code, safe_globals)
        
        fig = plt.gcf()
        if fig.get_axes():
            buffer = BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            return image_base64
        else:
            return "No plot was generated"
            
    except Exception as e:
        plt.close('all')
        return f"Error executing plot code: {str(e)}"

def scrape_multiple_urls(urls: list) -> dict:
    """Your existing URL scraping function."""
    # Your existing implementation
    return {}

# Example usage with model comparison
def compare_models_example():
    """Test with format-specific questions."""
    
    context_data = {
        "csvdata": ["Product,Sales,Region\nLaptop,1200,North\nMouse,300,South\nKeyboard,500,North"],
        "text": ["Q1 sales data for electronics"]
    }
    
    # Example 1: Specific JSON format requested
    question1 = """Answer these questions and return response in this JSON format:
    {
        "total_sales": "number",
        "best_product": "product name",
        "chart_needed": "yes/no"
    }
    1. What are the total sales?
    2. Which product sold the most?
    3. Do we need a sales chart?"""
    
    # Example 2: Plot requested with specific format
    question2 = """Create a bar chart of sales by product. Return in format:
    {
        "summary": "brief description",
        "plot": "matplotlib code here"
    }"""
    
    print("Testing format-specific responses...")
    
    result1 = process_questions_updated(question1, context_data, "gpt-4.1")
    print("Result 1:", json.dumps(result1, indent=2))
    
    result2 = process_questions_updated(question2, context_data, "gpt-4.1") 
    print("Result 2:", json.dumps(result2, indent=2))

if __name__ == "__main__":
    compare_models_example()