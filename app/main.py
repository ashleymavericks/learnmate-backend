from fastapi import FastAPI
from app.router import router
from app.db_adapter import create_db_and_tables
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_event_handler("startup", create_db_and_tables)

app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
@app.get("/")
async def root():
    return {"message": "Welcome to learnmate-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)