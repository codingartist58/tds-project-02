from datetime import datetime
import io
import json
import re
from PIL import Image   
from typing import Dict, List, Any
from fastapi import FastAPI, Request
#from starlette.datastructures import UploadFile
import logging
import os
import shutil
import csv
import pytesseract
import requests
from bs4 import BeautifulSoup
import pdfplumber

from src.utils.ai import process_questions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

INCOMING_DIR = "incoming"
QUESTIONS_DIR = os.path.join(INCOMING_DIR, "questions")
os.makedirs(QUESTIONS_DIR, exist_ok=True)

def extract_urls(text: str) -> List[str]:
    """Extract URLs from a given text."""
    url_pattern = r'https?://\S+'
    return re.findall(url_pattern, text)



def extract_csv(file_path: str) -> List[Dict[str, Any]]:
    """Read CSV file and return a list of dictionaries."""
    try:
        data = []
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            # Try to detect delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            reader = csv.DictReader(csvfile, delimiter=delimiter)
            for row in reader:
                # Clean up whitespace in keys and values
                cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v 
                             for k, v in row.items() if k is not None}
                data.append(cleaned_row)

        logger.info(f"Successfully extracted {len(data)} rows from CSV: {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {e}")
        return []

def extract_image(file_bytes: bytes) -> str:
    """
    Extract text from an image file using OCR.
    Args:
        file_bytes: The raw image bytes.
    Returns:
        Extracted text as a string.
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"Error extracting text from image: {str(e)}"

def extract_pdf(file_path: str) -> str:
    "Extract only tables from pdf"
    all_data = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table:
                    headers = table[0]
                    for row in table[1:]:
                        row_dict = {headers[i]: row[i] for i in range(len(headers))}
                        all_data.append(row_dict)
    return all_data

        
def process_incoming_files(saved_files: List[str], questions_text: str) -> Dict[str, Any]:
    """Process all saved files and return structured JSON."""
    extracted_data = {
        #"url_contents": "",
        "urls": [],
        "csvdata": [],
        "text": "",
        "pdfdata": [],
        "images_text": []
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
        # handling csv files
        file_path_low = file_path.lower()

        # handling csv files
        if file_path_low.endswith(".csv"):
            extracted_data["csvdata"].extend(extract_csv(file_path))

        elif file_path_low.endswith(".txt") and not (file_path_low.endswith("questions.txt") or file_path_low.endswith("question.txt")):
            with open(file_path, "r", encoding="utf-8") as f:
                extracted_data["text"] += f.read() + "\n"

        # handling images
        elif file_path_low.startswith("image") or file_path.lower().endswith((".png", ".jpg", ".jpeg", ".tiff")):
            with open(file_path, "rb") as f:
                file_bytes = f.read()
                text = extract_image(file_bytes)
                extracted_data["images_text"].append(text)

        #handling pdf files
        elif file_path_low.endswith(".pdf"):
            pdf_text = extract_pdf(file_path)
            extracted_data["pdfdata"].append(pdf_text)

    return extracted_data


@app.get("/")
async def hello():
    return {"message": "Yipee!"}

@app.post("/api/")
async def analyze_task(request: Request):
    form = await request.form()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_directory = os.path.join("runs", f"run_{timestamp}")
    os.makedirs(run_directory, exist_ok=True)
    questions_text = None
    saved_files = []
    
    for field_name, value in form.items():
        if hasattr(value, "filename") and hasattr(value, "file"):
            

            # Save incoming files with timestamp
            base, ext = os.path.splitext(value.filename)
            new_filename = f"{base}{ext}"

            file_path = os.path.join(run_directory, new_filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(value.file, buffer)
            saved_files.append(file_path)

            value.file.seek(0)
            #buffer.flush()

            if value.filename == "questions.txt" or value.filename == "question.txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    questions_text = f.read()
                

    if not questions_text:
        return {"error": "questions.txt is required"}
    
    # Process files into JSON
    extracted_data = process_incoming_files(saved_files, questions_text)
    print(f"---[EXTRACTED]Extracted data: {extracted_data}")
    
    return {"extracted_data": "done!!!"}

    # write the extracted_data into a file
    extracted_data_path = os.path.join(
        run_directory,
        f"extracted_data.json"
    )
    with open(extracted_data_path, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f)

    #return {"The end": "Extraction complete"}

    llm_response = process_questions(questions_text, extracted_data)

    # Save LLM response in /incoming/questions/ with matching timestamp
    response_path = os.path.join(
        run_directory,
        f"response.txt"
    )
    with open(response_path, "w", encoding="utf-8") as f:
        f.write(str(llm_response))


    return llm_response

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))  # fallback for local dev
    uvicorn.run("src.main:app", host="0.0.0.0", port=port)


    