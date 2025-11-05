import os

from aws_cdk import (
    App,
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_apigateway as apigateway,
)
from aws_cdk import (
    aws_certificatemanager as acm,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_lambda as lambda_,
)
from aws_cdk import (
    aws_logs as logs,
)
from aws_cdk import (
    aws_s3 as s3,
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
            description="Calls OpenAI, caches responses and returns the result",
            # code
            handler="handler.handler",
            code=lambda_.Code.from_asset("./package.zip"),
            # runtime
            memory_size=128,
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(120),
            # debugging
            profiling=True,
            tracing=lambda_.Tracing.ACTIVE,
            # logging
            log_group=logs.LogGroup(
                self,
                "qsh-logs-function",
                log_group_name="qsh-logs-function",
                removal_policy=RemovalPolicy.DESTROY,
                retention=logs.RetentionDays.THREE_DAYS,
            ),
            # environment
            environment={
                "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
                "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
                "S3_BUCKET_NAME": bucket.bucket_name,
            },
            # policies
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
            description="API Gateway for qsh",
            handler=function,  # type: ignore
            # proxy
            proxy=False,
            # auth
            default_method_options=apigateway.MethodOptions(
                authorization_type=apigateway.AuthorizationType.NONE,
            ),
            # logging
            cloud_watch_role=True,
            cloud_watch_role_removal_policy=RemovalPolicy.DESTROY,
            # deploy
            deploy=True,
            retain_deployments=False,
            deploy_options=apigateway.StageOptions(
                stage_name="v0",
                description="The main stage of the API",
                # debugging
                metrics_enabled=True,
                tracing_enabled=True,
                data_trace_enabled=True,
                # limits
                throttling_rate_limit=100,
                throttling_burst_limit=100,
                # logging
                logging_level=apigateway.MethodLoggingLevel.INFO,
                access_log_destination=apigateway.LogGroupLogDestination(
                    logs.LogGroup(
                        self,
                        "qsh-logs-api",
                        log_group_name="qsh-logs-api",
                        removal_policy=RemovalPolicy.DESTROY,
                        retention=logs.RetentionDays.THREE_DAYS,
                    )
                ),  # type: ignore
                access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True,
                ),
            ),
        )

        api.root.add_method("POST")

        api.root.add_resource("docs").add_method("GET")
        api.root.add_resource("redoc").add_method("GET")
        api.root.add_resource("openapi.json").add_method("GET")

        domain = api.add_domain_name(
            "qsh-domain",
            domain_name="qsh.jmeyer.dev",
            endpoint_type=apigateway.EndpointType.EDGE,
            certificate=acm.Certificate(
                self,
                "qsh-certificate",
                domain_name="qsh.jmeyer.dev",
                validation=acm.CertificateValidation.from_dns(),
            ),
        )


app = App()
QSH(app, "qsh")
app.synth()
