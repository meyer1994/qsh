import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import handler


class TestHandler(unittest.IsolatedAsyncioTestCase):
    @patch("handler.Mangum")
    def test_handler(self, *args):
        event = {"TEST": "TEST"}
        context = MagicMock()

        response = handler.handler(event, context)

        self.assertEqual(response, handler.Mangum.return_value.return_value)
        handler.Mangum.assert_called_once_with(handler.app)

    @patch("handler.hishel.AsyncS3Storage", autospec=True)
    async def test_dep_llm(self, *args):
        cfg = MagicMock()
        cfg.S3_BUCKET_NAME = "test-bucket"
        cfg.OPENAI_API_KEY = "test-api-key"

        async for llm in handler.dep_llm(cfg):
            self.assertEqual(llm.model_name, "gpt-4o-mini")

        handler.hishel.AsyncS3Storage.assert_called_once_with(
            bucket_name=cfg.S3_BUCKET_NAME,
        )

    async def test_post_with_system_prompt(self, *args):
        ctx = MagicMock()
        ctx.llm = AsyncMock()
        ctx.user = b"Generate a simple hello world program."
        ctx.system = b"Provide a Python program."

        structured = ctx.llm.with_structured_output.return_value
        structured.ainvoke.return_value = handler.Result(
            reasoning="short reasoning",
            program="print('hello')",
        )

        await handler.post(ctx)

        ctx.llm.with_structured_output.assert_called_once_with(handler.Result)
        structured.ainvoke.assert_awaited_once_with([
            handler.SystemMessage(content="Provide a Python program."),
            handler.HumanMessage(content="Generate a simple hello world program."),
        ])

    async def test_post_without_system_prompt(self, *args):
        ctx = MagicMock()
        ctx.llm = AsyncMock()
        ctx.user = b"Generate a simple hello world program."
        ctx.system = b"@@@@"

        structured = ctx.llm.with_structured_output.return_value
        structured.ainvoke.return_value = handler.Result(
            reasoning="short reasoning",
            program="print('hello')",
        )

        await handler.post(ctx)

        ctx.llm.with_structured_output.assert_called_once_with(handler.Result)
        structured.ainvoke.assert_awaited_once_with([
            handler.HumanMessage(content="Generate a simple hello world program."),
        ])
