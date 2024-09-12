from contextlib import asynccontextmanager
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-2024-08-06"
OPENAI_MAX_TOKEN_COUNT = 16384

@asynccontextmanager
async def openai_client_context():
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        yield client
    finally:
        await client.close()


async def openai_chat_completion(
    payload: dict, output_schema: BaseModel, temperature: float = 1.0
):
    async with openai_client_context() as client:
        openai_response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=payload["messages"],
            max_tokens=OPENAI_MAX_TOKEN_COUNT,
            response_format={
                "type": "json_object",
                "schema": output_schema.model_json_schema()
            }
        )
    return openai_response
