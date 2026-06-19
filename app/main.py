# app/main.py

from fastapi import FastAPI
from app.api.endpoints import router as api_router  # if you have routes defined

app = FastAPI()

# Optional: include API routes if you defined them
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or set to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

