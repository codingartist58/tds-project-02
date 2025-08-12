from datetime import datetime
import re
from typing import Dict, List, Any
from fastapi import FastAPI, Request
#from starlette.datastructures import UploadFile
import logging
import os
import shutil
import csv
import requests
from bs4 import BeautifulSoup


from utils.ai import process_questions



app = FastAPI()

INCOMING_DIR = "incoming"
QUESTIONS_DIR = os.path.join(INCOMING_DIR, "questions")
os.makedirs(QUESTIONS_DIR, exist_ok=True)

def extract_urls(text: str) -> List[str]:
    """Extract URLs from a given text."""
    url_pattern = r'https?://\S+'
    return re.findall(url_pattern, text)

def scrape_url(url: str):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Extract visible text
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        return None

def extract_csv(file_path: str) -> List[Dict[str, Any]]:
    """Read CSV file and return a list of dictionaries."""
    data = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

def process_incoming_files(saved_files: List[str], questions_text: str) -> Dict[str, Any]:
    """Process all saved files and return structured JSON."""
    extracted_data = {
        #"url_contents": "",
        "urls": [],
        "questions": questions_text,
        "csvdata": []
    }
    urls = extract_urls(questions_text) if questions_text else []
    #extracted_data["url_contents"] += content + "\n" if content else 
    # If URLs found, scrape them
    
    """     
        if len(urls) != 0:
        for url in urls:
            content = scrape_url(url)
            extracted_data["url_contents"] += content + "\n" if content else """
    
    extracted_data["urls"] = urls

    for file_path in saved_files:
        if file_path.endswith(".csv"):
            extracted_data["csvdata"].extend(extract_csv(file_path))
        # Later: Add handlers for images, PDFs, etc.

    return extracted_data




@app.post("/api/")
async def analyze_task(request: Request):
    form = await request.form()

    questions_text = None
    saved_files = []

    for field_name, value in form.items():
        if hasattr(value, "filename") and hasattr(value, "file"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save incoming files with timestamp
            base, ext = os.path.splitext(value.filename)
            new_filename = f"{base}_{timestamp}{ext}"

            file_path = os.path.join(INCOMING_DIR, new_filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(value.file, buffer)
            saved_files.append(file_path)

            if value.filename == "questions.txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    questions_text = f.read()


                # Save questions into /incoming/questions/ with timestamp
                #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                questions_copy_path = os.path.join(
                    QUESTIONS_DIR,
                    f"questions_{timestamp}.txt"
                )
                with open(questions_copy_path, "w", encoding="utf-8") as f:
                    f.write(questions_text)

    if not questions_text:
        return {"error": "questions.txt is required"}
    
    # Process files into JSON
    extracted_data = process_incoming_files(saved_files, questions_text)
    print(f"---[EXTRACTED]Extracted data: {extracted_data}")

    print(f"----------sending llm {questions_text}")
    
    llm_response = process_questions(questions_text, extracted_data)

    # Save LLM response in /incoming/questions/ with matching timestamp
    response_path = os.path.join(
        QUESTIONS_DIR,
        f"response_{timestamp}.txt"
    )
    with open(response_path, "w", encoding="utf-8") as f:
        f.write(llm_response)



    return {
        "message": "Files saved and processed",
        "llm_response": llm_response
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8020, reload=True)
    