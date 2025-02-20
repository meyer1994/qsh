from dataclasses import dataclass
from typing import Annotated

from aws_lambda_powertools import Logger, Metrics, Tracer
from fastapi import Depends, FastAPI, File
from fastapi.responses import PlainTextResponse
from mangum import Mangum
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    OPENAI_API_KEY: str


logger = Logger(service="qsh-service")
metrics = Metrics(namespace="qsh")
tracer = Tracer(service="qsh-service")

app = FastAPI(title="QSH Service")


async def dep_config() -> Config:
    return Config()  # type: ignore


async def dep_openai(cfg: Annotated[Config, Depends(dep_config)]) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=cfg.OPENAI_API_KEY)


@dataclass
class Context:
    openai: Annotated[AsyncOpenAI, Depends(dep_openai)]
    user: Annotated[bytes, File(alias="u", min_length=4, max_length=1024)]
    system: Annotated[bytes, File(alias="s", min_length=4, max_length=1024)] = b"@@@@"


class Result(BaseModel):
    reasoning: Annotated[
        str, Field(description="The reasoning behind the program. At most 15 words")
    ]
    program: Annotated[str, Field(description="The generated program")]


@app.post("/", response_class=PlainTextResponse)
@tracer.capture_method
async def post(ctx: Annotated[Context, Depends(Context)]) -> str:
    prompt_user: str = ctx.user.decode("utf-8")
    prompt_system: str = ctx.system.decode("utf-8")

    logger.info(f"Received prompt: {prompt_user}")
    logger.info(f"Received system: {prompt_system}")

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
    assert result is not None

    logger.info("Generated program successfully")
    logger.info("Reasoning: %s", result.reasoning)

    return result.program + "\n"


handler = Mangum(app)
