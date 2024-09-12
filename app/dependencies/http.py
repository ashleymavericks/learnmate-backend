from typing import Any
from fastapi import HTTPException
import aiohttp

async def get(url: str, headers: dict = None) -> Any:
    async with aiohttp.ClientSession() as client:
        async with client.get(url, headers=headers) as response:
            if response.status != 200:
                raise HTTPException(
                    status_code=response.status,
                    detail={
                        "message_code": "GET_REQUEST_FAILURE",
                        "message_text": await response.text(),
                    }
                )
            return await response.json()

async def post(url: str, data: Any = None, form_data: dict = None, headers: dict = None, auth: Any = None) -> Any:
    async with aiohttp.ClientSession() as client:
        async with client.post(url, json=data, data=form_data, headers=headers, auth=auth) as response:
            if response.status not in [200, 201, 202]:
                raise HTTPException(
                    status_code=response.status,
                    detail={
                        "message_code": "POST_REQUEST_FAILURE",
                        "message_text": await response.text(),
                    }
                )
            return await response.json()
        