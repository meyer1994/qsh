import json
import logging

from mangum import Mangum

from qsh.app import app

logger = logging.getLogger(__name__)


def handler(event, context):
    logger.info(json.dumps(event))
    handler = Mangum(app)
    return handler(event, context)
