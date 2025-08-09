import os
import shutil
import re
import csv
from io import StringIO, BytesIO
from PIL import Image
import pytesseract
import json

INCOMING_DIR = "./incoming"

def extract_info_from_files(files):
    result = {
        "urls": [],
        "questions": [],
        "csvdata": []
    }
    url_pattern = re.compile(r"https?://\S+")

    for file_path in files:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            result["urls"].extend(url_pattern.findall(text))
            if os.path.basename(file_path) == "questions.txt":
                result["questions"].extend(
                    [line.strip() for line in text.splitlines() if line.strip()]
                )

        elif ext == ".csv":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                result["csvdata"].extend(list(reader))

        elif ext in (".jpg", ".jpeg", ".png"):
            with open(file_path, "rb") as img_file:
                img = Image.open(BytesIO(img_file.read()))
                text = pytesseract.image_to_string(img)
                result["urls"].extend(url_pattern.findall(text))

    # Deduplicate
    result["urls"] = sorted(set(result["urls"]))
    result["questions"] = sorted(set(result["questions"]))

    # write the json to a file
    output_path = "./extracted_info.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    return result


if __name__ == "__main__":
    # Example usage
    files = [os.path.join(INCOMING_DIR, f) for f in os.listdir(INCOMING_DIR)]
    extracted_info = extract_info_from_files(files)

    #print("Extracted URLs:", extracted_info["urls"])
    #print("Extracted Questions:", extracted_info["questions"])
    #print("Extracted CSV Data:", extracted_info["csvdata"])