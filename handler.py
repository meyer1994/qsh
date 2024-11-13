import json
import logging
from typing import Any

from mangum import Mangum
from mangum.types import LambdaContext

from qsh.app import app

logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    logger.info(json.dumps(event))
    handler = Mangum(app)
    return handler(event, context)
