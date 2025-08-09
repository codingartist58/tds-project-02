import re
from typing import Dict, List, Any
from fastapi import FastAPI, Request
from starlette.datastructures import UploadFile
import logging
import os
import shutil
import csv


from utils.ai import process_questions

app = FastAPI()

INCOMING_DIR = "incoming"
os.makedirs(INCOMING_DIR, exist_ok=True)

def extract_urls(text: str) -> List[str]:
    """Extract URLs from a given text."""
    url_pattern = r'https?://\S+'
    return re.findall(url_pattern, text)

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
    urls = extract_urls(questions_text) if questions_text else []
    csv_data = []

    for file_path in saved_files:
        if file_path.endswith(".csv"):
            csv_data.extend(extract_csv(file_path))
        # Later: Add handlers for images, PDFs, etc.

    return {
        "urls": urls,
        "csvdata": csv_data
    }




@app.post("/api/")
async def analyze_task(request: Request):
    form = await request.form()

    questions_text = None
    saved_files = []

    for field_name, value in form.items():
        if hasattr(value, "filename") and hasattr(value, "file"):
            file_path = os.path.join(INCOMING_DIR, value.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(value.file, buffer)
            saved_files.append(file_path)

            if value.filename == "questions.txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    questions_text = f.read()

    if not questions_text:
        return {"error": "questions.txt is required"}
    
    # Process files into JSON
    extracted_data = process_incoming_files(saved_files, questions_text)


    print(f"----------sending llm {questions_text}")
    llm_response = process_questions(questions_text, extracted_data)

    response_path = os.path.join(INCOMING_DIR, "response.txt")
    with open(response_path, "w", encoding="utf-8") as f:
        f.write(llm_response)

    return {
        "message": "Files saved and processed",
        "llm_response": llm_response
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8020, reload=True)
    