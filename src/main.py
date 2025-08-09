import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
#from utils.agent_controller import process_task

import uvicorn

app = FastAPI()

INCOMING_DIR = "incoming"
os.makedirs(INCOMING_DIR, exist_ok=True)  # create folder if it doesn't exist

@app.post("/api/")
async def analyze_task(files: List[UploadFile] = File(...)):
    # Save the required questions.txt file
    for file in files:
        file_path = os.path.join(INCOMING_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    # Save any additional files
    
    return {"message": "Files saved to incoming/"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8020, reload=True)
    