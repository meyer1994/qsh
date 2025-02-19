from dataclasses import dataclass
from typing import Annotated

from aws_lambda_powertools import Logger, Metrics, Tracer
from fastapi import Body, Depends, FastAPI
from fastapi.responses import PlainTextResponse
from mangum import Mangum
from openai import AsyncOpenAI
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
    prompt: Annotated[str, Body()]
    openai: Annotated[AsyncOpenAI, Depends(dep_openai)]


class Result(BaseModel):
    reasoning: Annotated[str, Field(description="The reasoning behind the program")]
    program: Annotated[str, Field(description="The generated program")]


@app.post("/", response_class=PlainTextResponse)
@tracer.capture_method
async def post(ctx: Annotated[Context, Depends(Context)]):
    logger.info(f"Received prompt: {ctx.prompt}")

    response = await ctx.openai.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": ctx.prompt}],
        max_tokens=150,
        temperature=0.5,
        response_format=Result,
    )

    result = response.choices[0].message.parsed
    assert result is not None

    logger.info("Generated program successfully")
    logger.debug("Reasoning: %s", result.reasoning)
    logger.debug("Program: %s", result.program)

    return PlainTextResponse(result.program)


handler = Mangum(app)
