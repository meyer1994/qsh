import os

from aws_cdk import (
    App,
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
)


class QSH(Stack):
    def __init__(self, scope: App, id: str):
        super().__init__(scope, id)

        function = lambda_.Function(
            self,
            f"{id}-lambda",
            runtime=lambda_.Runtime.PYTHON_3_13,
            code=lambda_.Code.from_asset("./package.zip"),
            handler="handler.handler",
            memory_size=128,
            timeout=Duration.seconds(15),
            environment={
                "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
            },
        )

        api = apigateway.LambdaRestApi(
            self,
            f"{id}-api",
            rest_api_name=f"{id} API",
            handler=function,
            proxy=True,
        )


app = App()
QSH(app, "qsh")
app.synth()
