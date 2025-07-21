from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

@app.post('/api/')
async def handle_request():
    return {"message": "Request received successfully"}