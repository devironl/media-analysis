from aws_cdk import core, aws_lambda, aws_secretsmanager, aws_apigateway, aws_events, aws_events_targets
from stacks.stack_utils import *


class AnnotationStack(core.Stack):
    
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        code_path = "./lambda/annotation"

        """ Define Layers """
        
        requests_layer = get_layer(self, "requests")
        pymongo_layer = get_layer(self, "pymongo")

        secret = get_secret(self)
        
        """ Define Lambdas """
        
        # TR unique
        textrazor_lambda = get_lambda(
            scope=self,
            name="textrazor_lambda",
            env_dict={
                "SECRET_ARN": secret.secret_arn,
            },
            layers=[pymongo_layer, requests_layer],
            code_path=code_path,
            reserved_concurrent_executions=4
        )

        # RT on DB
        annotation_lambda = get_lambda(
            scope=self,
            name="annotation_lambda",
            env_dict={
                "SECRET_ARN": secret.secret_arn,
                "TEXTRAZOR_LAMBDA": textrazor_lambda.function_name
            },
            layers=[pymongo_layer, requests_layer],
            code_path=code_path,
        )

        secret.grant_read(textrazor_lambda)
        secret.grant_read(annotation_lambda)
        
        textrazor_lambda.grant_invoke(annotation_lambda)

        """        
        # Cron every 2 hours
        aws_events.Rule(
            scope=self,
            id='crawler-cron',
            schedule=aws_events.Schedule.rate(core.Duration.hours(4)),
            targets=[aws_events_targets.LambdaFunction(feed_extractor_lambda)]
        )
        """
        
