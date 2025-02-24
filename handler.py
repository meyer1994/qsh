from dataclasses import dataclass
import json
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, File
from fastapi.responses import PlainTextResponse
import hishel
from mangum import Mangum
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = FastAPI(title="qsh")


class Config(BaseSettings):
    OPENAI_API_KEY: str
    S3_BUCKET_NAME: str


def dep_config() -> Config:
    return Config()  # type: ignore


async def dep_openai(cfg: Annotated[Config, Depends(dep_config)]):
    controller = hishel.Controller(cacheable_methods=["POST"], force_cache=True)
    storage = hishel.AsyncS3Storage(bucket_name=cfg.S3_BUCKET_NAME)
    client = hishel.AsyncCacheClient(storage=storage, controller=controller)
    openai = AsyncOpenAI(api_key=cfg.OPENAI_API_KEY, http_client=client)

    async with client, openai:
        yield openai


@dataclass
class Context:
    openai: Annotated[AsyncOpenAI, Depends(dep_openai)]
    user: Annotated[bytes, File(alias="u", min_length=4, max_length=1024)]
    system: Annotated[bytes, File(alias="s", min_length=4, max_length=1024)] = b"@@@@"


class Result(BaseModel):
    reasoning: Annotated[str, Field(description="The reasoning. At most 15 words")]
    program: Annotated[str, Field(description="The generated program")]


@app.post("/", response_class=PlainTextResponse)
async def post(ctx: Annotated[Context, Depends(Context)]) -> str:
    prompt_user = ctx.user.decode()
    prompt_system = ctx.system.decode()

    logger.info("Received prompt: %s", prompt_user)
    logger.info("Received system: %s", prompt_system)

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": prompt_system},
        {"role": "user", "content": prompt_user},
    ]

    if prompt_system == "@@@@":
        logger.info("No system prompt provided")
        messages.pop(0)

    response = await ctx.openai.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1024,
        temperature=0.5,
        response_format=Result,
    )

    result = response.choices[0].message.parsed
    assert result is not None, "No result from OpenAI"

    logger.info("Generated program successfully")
    logger.debug("Reasoning: %s", result.reasoning)
    logger.debug("Program: %s", result.program)

    return result.program + "\n"


def handler(event, context) -> dict:
    logger.debug(json.dumps(event))
    function = Mangum(app)
    return function(event, context)
