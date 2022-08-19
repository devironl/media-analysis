from constructs import Construct
from aws_cdk import Stack, Duration
from aws_cdk import aws_lambda
from aws_cdk import aws_secretsmanager
from aws_cdk import aws_apigateway
from aws_cdk import aws_events, aws_events_targets
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from config import project_id, secret_name, account_id, region




class AnnotationStack(Stack):
    
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        code_path = "./lambda/annotation"
    

        secret = aws_secretsmanager.Secret.from_secret_attributes(
            scope=self,
            id=f"{project_id}-secret",
            secret_partial_arn=f"arn:aws:secretsmanager:{region}:{account_id}:secret:{secret_name}"
        )
        
        """ Define Lambdas """
        
        # TR unique
        textrazor_lambda = PythonFunction(
            scope=self,
            id=f"{project_id}-textrazor-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            function_name=f"{project_id}-textrazor-lambda",
            entry=code_path,
            index="textrazor_lambda.py",
            environment={
                "SECRET_ARN": secret.secret_arn,
            },
            timeout=Duration.seconds(900),
            memory_size=3008,
            reserved_concurrent_executions=4
        )

        # TR on DB
        annotation_lambda = PythonFunction(
            scope=self,
            id=f"{project_id}-annotation-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            function_name=f"{project_id}-annotation-lambda",
            entry=code_path,
            index="annotation_lambda.py",
            environment={
                "SECRET_ARN": secret.secret_arn,
            },
            timeout=Duration.seconds(900),
            memory_size=3008,
            reserved_concurrent_executions=4
        )

        secret.grant_read(textrazor_lambda)
        secret.grant_read(annotation_lambda)
        
        textrazor_lambda.grant_invoke(annotation_lambda)

                
        # Cron every 4 hours
        aws_events.Rule(
            scope=self,
            id=f'{project_id}-annotation-cron',
            schedule=aws_events.Schedule.rate(Duration.hours(4)),
            targets=[aws_events_targets.LambdaFunction(annotation_lambda)]
        )
        
        
