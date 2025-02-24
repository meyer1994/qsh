import os

from aws_cdk import (
    App,
    RemovalPolicy,
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_s3 as s3,
    aws_iam as iam,
)


class QSH(Stack):
    def __init__(self, scope: App, id: str):
        super().__init__(scope, id)

        bucket = s3.Bucket(
            self,
            "bucket",
            bucket_name="qsh-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            lifecycle_rules=[
                s3.LifecycleRule(
                    enabled=True,
                    expiration=Duration.days(1),
                )
            ],
        )

        function = lambda_.Function(
            self,
            "function",
            function_name="qsh-function",
            runtime=lambda_.Runtime.PYTHON_3_13,
            code=lambda_.Code.from_asset("./package.zip"),
            handler="handler.handler",
            memory_size=128,
            timeout=Duration.seconds(15),
            environment={
                "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
                "S3_BUCKET_NAME": bucket.bucket_name,
            },
            initial_policy=[
                iam.PolicyStatement(
                    actions=["s3:PutObject", "s3:GetObject"],
                    resources=[f"{bucket.bucket_arn}/*"],
                )
            ],
        )

        api = apigateway.LambdaRestApi(
            self,
            "qsh-api",
            rest_api_name="qsh-api",
            handler=function,  # type: ignore
            proxy=False,
            deploy=True,
            retain_deployments=False,
            cloud_watch_role=True,
            cloud_watch_role_removal_policy=RemovalPolicy.DESTROY,
            default_method_options=apigateway.MethodOptions(
                authorization_type=apigateway.AuthorizationType.NONE,
            ),
            deploy_options=apigateway.StageOptions(
                stage_name="v0",
                metrics_enabled=True,
                tracing_enabled=True,
                data_trace_enabled=True,
                logging_level=apigateway.MethodLoggingLevel.INFO,
            ),
        )

        api.root.add_method("POST")


app = App()
QSH(app, "qsh")
app.synth()
