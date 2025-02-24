import unittest
from unittest.mock import MagicMock, patch

import handler


class TestHandler(unittest.TestCase):
    @patch("handler.Mangum")
    def test_handler(self, _):
        event = {"TEST": "TEST"}
        context = MagicMock()

        response = handler.handler(event, context)

        self.assertEqual(response, handler.Mangum.return_value.return_value)
        handler.Mangum.assert_called_once_with(handler.app)
