from fastapi import FastAPI
from app.router import router
from app.db_adapter import create_db_and_tables

app = FastAPI()

app.add_event_handler("startup", create_db_and_tables)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app.main, host="0.0.0.0", port=8000)