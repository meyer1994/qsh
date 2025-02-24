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
    async def test_dep_openai(self, *args):
        cfg = MagicMock()
        cfg.S3_BUCKET_NAME = "test-bucket"
        cfg.OPENAI_API_KEY = "test-api-key"

        async for openai in handler.dep_openai(cfg):
            self.assertEqual(openai.api_key, cfg.OPENAI_API_KEY)

        handler.hishel.AsyncS3Storage.assert_called_once_with(
            bucket_name=cfg.S3_BUCKET_NAME,
        )

    async def test_post_with_system_prompt(self, *args):
        ctx = MagicMock()
        ctx.openai = AsyncMock()
        ctx.user = b"Generate a simple hello world program."
        ctx.system = b"Provide a Python program."

        await handler.post(ctx)

        ctx.openai.beta.chat.completions.parse.assert_awaited_once_with(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Provide a Python program."},
                {"role": "user", "content": "Generate a simple hello world program."},
            ],
            max_tokens=1024,
            temperature=0.5,
            response_format=handler.Result,
        )

    async def test_post_without_system_prompt(self, *args):
        ctx = MagicMock()
        ctx.openai = AsyncMock()
        ctx.user = b"Generate a simple hello world program."
        ctx.system = b"@@@@"

        await handler.post(ctx)

        ctx.openai.beta.chat.completions.parse.assert_awaited_once_with(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Generate a simple hello world program."},
            ],
            max_tokens=1024,
            temperature=0.5,
            response_format=handler.Result,
        )
