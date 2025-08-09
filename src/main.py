from fastapi import FastAPI, Request, UploadFile
import os
import shutil

app = FastAPI()

INCOMING_DIR = "incoming"
os.makedirs(INCOMING_DIR, exist_ok=True)

@app.post("/api/")
async def analyze_task(request: Request):
    form = await request.form()

    for field_name, file in form.items():
        if isinstance(file, UploadFile):
            save_path = os.path.join("incoming", file.filename)
            os.makedirs("incoming", exist_ok=True)
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            print(f"Saved {file.filename} (field: {field_name})")

    return {"message": "Files saved"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8020, reload=True)
    