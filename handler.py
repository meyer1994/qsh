import enum
import json
import logging
import logging.config
from dataclasses import dataclass
from typing import Annotated
from uuid import uuid4

import uvicorn
import uvicorn.logging
from asgi_correlation_id import CorrelationIdFilter, CorrelationIdMiddleware
from fastapi import Depends, FastAPI, File, Query
from fastapi.responses import PlainTextResponse
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from mangum import Mangum
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = FastAPI(title="qsh")

app.add_middleware(
    CorrelationIdMiddleware,
    generator=lambda: "%s" % uuid4(),
)


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    S3_BUCKET_NAME: str
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str


def dep_config() -> Config:
    return Config()  # type: ignore


class Models(enum.StrEnum):
    CLAUDE_SONNET_4_5 = "claude-sonnet-4-5"
    CLAUDE_HAIKU_4_5 = "claude-haiku-4-5"
    CLAUDE_OPUS_4_1 = "claude-opus-4-1"
    CLAUDE_SONNET_4 = "claude-sonnet-4"
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet"
    CLAUDE_OPUS_4 = "claude-opus-4"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    O3 = "o3"
    O3_DEEP_RESEARCH = "o3-deep-research"
    O4_MINI_DEEP_RESEARCH = "o4-mini-deep-research"
    GPT_OSS_120B = "gpt-oss-120b"
    GPT_OSS_20B = "gpt-oss-20b"


SENTINEL = b"@@@@@@"


@dataclass
class Context:
    cfg: Annotated[Config, Depends(dep_config)]

    # data
    user: Annotated[bytes, File(alias="u", min_length=4, max_length=1024 * 10)]
    system: Annotated[bytes, File(alias="s", min_length=4, max_length=1024 * 10)] = SENTINEL

    # configs
    model: Annotated[Models, Query(alias="m")] = Models.GPT_4_1_MINI
    temperature: Annotated[float, Query(alias="t")] = 0.5


class Result(BaseModel):
    reasoning: Annotated[str, Field(description="The reasoning. At most 15 words")]
    program: Annotated[str, Field(description="The generated program")]


@app.post("/", response_class=PlainTextResponse)
async def post(ctx: Annotated[Context, Depends(Context)]) -> str:
    logger.info("Received model: %s", ctx.model)
    logger.info("Received temperature: %s", ctx.temperature)

    llm = init_chat_model(
        model=ctx.model.value,
        temperature=ctx.temperature,
        max_tokens=1024 * 10,
    )

    prompt_user = ctx.user.decode()
    prompt_system = ctx.system.decode()

    logger.info("Received prompt: %s", prompt_user[:32])
    logger.info("Received system: %s", prompt_system[:32])

    messages: list[SystemMessage | HumanMessage] = []

    if ctx.system == SENTINEL:
        logger.info("No system prompt provided")
        messages.append(HumanMessage(prompt_user))
    else:
        messages.append(SystemMessage(prompt_system))
        messages.append(HumanMessage(prompt_user))

    llms = llm.with_structured_output(Result)  # type: ignore
    result: Result = await llms.ainvoke(messages)  # type: ignore

    logger.info("Generated program successfully")
    logger.info("Reasoning: %s", result.reasoning[:32])
    logger.info("Program: %s", result.program[:32])

    # add extra line for better terminal usage. otherwise, the next command
    # would appear after the curl ouput, instead of the new line
    return result.program + "\n"


def handler(event, context) -> dict:
    logger.debug(json.dumps(event))
    function = Mangum(app)
    return function(event, context)


logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation_id": {
                "()": CorrelationIdFilter,
                "uuid_length": 8,
            },
        },
        "formatters": {
            "access": {
                "use_colors": True,
                "datefmt": r"%Y-%m-%d %H:%M:%S",
                "()": uvicorn.logging.AccessFormatter,
                "fmt": "%(levelprefix)s [%(asctime)s] [%(correlation_id)s] - %(request_line)s %(status_code)s",
            },
            "default": {
                "use_colors": True,
                "datefmt": r"%Y-%m-%d %H:%M:%S",
                "()": uvicorn.logging.DefaultFormatter,
                "fmt": "%(levelprefix)s [%(asctime)s] [%(correlation_id)s] [%(module)s:%(lineno)s] - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "filters": ["correlation_id"],
                "class": logging.StreamHandler,
            },
            "access": {
                "formatter": "access",
                "filters": ["correlation_id"],
                "class": logging.StreamHandler,
            },
        },
        "loggers": {
            "handler": {
                "level": logging.DEBUG,
                "handlers": ["default"],
            },
            "uvicorn.access": {
                "level": logging.INFO,
                "handlers": ["access"],
            },
        },
    }
)
