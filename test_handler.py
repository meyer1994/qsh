import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage, SystemMessage

import handler


class TestHandler(unittest.IsolatedAsyncioTestCase):
    @patch("handler.Mangum")
    def test_handler(self, mock_mangum):
        event = {"TEST": "TEST"}
        context = MagicMock()

        mock_mangum.return_value.return_value = {"statusCode": 200}

        response = handler.handler(event, context)

        self.assertDictEqual(response, {"statusCode": 200})
        mock_mangum.assert_called_once_with(handler.app)
        mock_mangum.return_value.assert_called_once_with(event, context)  # type: ignore

    @patch("handler.init_chat_model")
    async def test_post_with_system_prompt(self, mock_init_chat_model):
        ctx = MagicMock()
        ctx.model = handler.Models.GPT_4_1_MINI
        ctx.temperature = 0.5
        ctx.user = b"Generate a simple hello world program."
        ctx.system = b"Provide a Python program."

        mock_structured = (
            # init_chat_model().with_structured_output()
            mock_init_chat_model.return_value.with_structured_output.return_value
        )

        mock_structured.ainvoke = AsyncMock(
            return_value=handler.Result(
                reasoning="short reasoning",
                program="print('hello')",
            )
        )

        result = await handler.post(ctx)

        self.assertEqual(result, "print('hello')\n")

        mock_init_chat_model.assert_called_once_with(
            model=ctx.model.value,
            temperature=ctx.temperature,
            max_tokens=1024,
        )
        mock_structured.ainvoke.assert_awaited_once_with(
            [
                SystemMessage(content="Provide a Python program."),
                HumanMessage(content="Generate a simple hello world program."),
            ]
        )

    @patch("handler.init_chat_model")
    async def test_post_without_system_prompt(self, mock_init_chat_model):
        ctx = MagicMock()
        ctx.model = handler.Models.GPT_4_1_MINI
        ctx.temperature = 0.5
        ctx.user = b"Generate a simple hello world program."
        ctx.system = handler.SENTINEL

        mock_structured = (
            # mock_llm.with_structured_output()
            mock_init_chat_model.return_value.with_structured_output.return_value
        )

        mock_structured.ainvoke = AsyncMock(
            return_value=handler.Result(
                reasoning="short reasoning",
                program="print('hello')",
            )
        )

        result = await handler.post(ctx)

        self.assertEqual(result, "print('hello')\n")

        mock_init_chat_model.assert_called_once_with(
            model=ctx.model.value,
            temperature=ctx.temperature,
            max_tokens=1024,
        )
        mock_structured.ainvoke.assert_awaited_once_with(
            [HumanMessage(content="Generate a simple hello world program.")],
        )
