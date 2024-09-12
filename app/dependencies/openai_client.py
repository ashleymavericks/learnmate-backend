import os
from typing import Union
from contextlib import asynccontextmanager
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv

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

async def openai_chat_completion(payload: dict, output_schema: Union[BaseModel | None] = None):
    async with openai_client_context() as client:
        if output_schema:
            openai_response = await client.beta.chat.completions.parse(
                model=OPENAI_MODEL,
                messages=payload["messages"],
                max_tokens=OPENAI_MAX_TOKEN_COUNT,
                response_format=output_schema
            )
            return openai_response.choices[0].message.content
        else:
            openai_response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=payload["messages"],
                max_tokens=OPENAI_MAX_TOKEN_COUNT
            )
            return openai_response.choices[0].message.content
