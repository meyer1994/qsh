import enum
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from openai import APIError, AsyncClient
from pydantic import BaseModel

from qsh.prompts import get_completion_prompt

app = FastAPI(
    title="Code Completion API",
    description="API for code completion using GPT-4",
    version="1.0.0",
    default_response_class=StreamingResponse,
)
client = AsyncClient()

OPENAI_MODEL = "gpt-4o-mini"
MAX_TOKENS = 256


class Lang(enum.StrEnum):
    PY = "py"
    JS = "js"


async def stream_completion(prompt: str) -> AsyncGenerator[str, None]:
    """Stream the completion response from OpenAI."""
    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "system", "content": prompt}],
            stream=True,  # Enable streaming
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


class CompletionParams(BaseModel):
    """Request parameters for code completion."""

    q: str = Query(..., description="The code to complete", min_length=1, max_length=64)
    lang: Lang = Query(default=Lang.PY, description="The language of the code")


@app.get("/", response_model=str)
async def get_completion(
    params: Annotated[CompletionParams, Depends(CompletionParams)],
) -> StreamingResponse:
    """
    Get code completion suggestions.

    Args:
        params: The completion parameters including code and language.

    Returns:
        StreamingResponse: The completion response streamed from the API.
    """
    prompt = get_completion_prompt(language=params.lang, code=params.q)
    return StreamingResponse(
        stream_completion(prompt),
        media_type="text/plain",
    )
