from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
from utils.agent_controller import process_task

import uvicorn

app = FastAPI()

@app.post("/api/")
async def analyze_task(file: UploadFile):
    task_text = await file.read()
    result = process_task(task_text.decode("utf-8"))
    return JSONResponse(content=result)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8020, reload=True)
