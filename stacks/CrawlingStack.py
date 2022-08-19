from constructs import Construct
from aws_cdk import Stack, Duration
from aws_cdk import aws_lambda
from aws_cdk import aws_secretsmanager
from aws_cdk import aws_apigateway
from aws_cdk import aws_events, aws_events_targets
from aws_cdk import aws_iam
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from config import project_id, secret_name, account_id, region, log_email


class CrawlingStack(Stack):
    
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        code_path = "./lambda/crawling"

        secret = aws_secretsmanager.Secret.from_secret_attributes(
            scope=self,
            id=f"{project_id}-secret",
            secret_partial_arn=f"arn:aws:secretsmanager:{region}:{account_id}:secret:{secret_name}"
        )
        
        """ Define Lambdas """
        
        # Crawl article
        article_lambda = PythonFunction(
            scope=self,
            id=f"{project_id}-article-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            function_name=f"{project_id}-article-lambda",
            entry=code_path,
            index="article_lambda.py",
            environment={
                "SECRET_ARN": secret.secret_arn,
            },
            timeout=Duration.seconds(900),
            memory_size=3008,
            reserved_concurrent_executions=10
        )

        # Crawl RSS feed
        feedparser_lambda = PythonFunction(
            scope=self,
            id=f"{project_id}-feedparser-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            function_name=f"{project_id}-feedparser-lambda",
            entry=code_path,
            index="feedparser_lambda.py",
            environment={
                "SECRET_ARN": secret.secret_arn,
                "ARTICLE_LAMBDA": article_lambda.function_name,
                "LOG_EMAIL": log_email,
            },
            timeout=Duration.seconds(900),
            memory_size=3008,
            reserved_concurrent_executions=10
        )
      

        # Extract RSS feeds
        feed_extractor_lambda = PythonFunction(
            scope=self,
            id=f"{project_id}-feed-extractor-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            function_name=f"{project_id}-feed-extractor-lambda",
            entry=code_path,
            index="feed_extractor_lambda.py",
            environment={
                "SECRET_ARN": secret.secret_arn,
                "FEEDPARSER_LAMBDA": feedparser_lambda.function_name
            },
            timeout=Duration.seconds(900),
            memory_size=3008,
        )
        
        secret.grant_read(article_lambda)
        secret.grant_read(feedparser_lambda)
        secret.grant_read(feed_extractor_lambda)

        
        feedparser_lambda.grant_invoke(feed_extractor_lambda)
        article_lambda.grant_invoke(feedparser_lambda)
        
        feedparser_lambda.add_to_role_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            resources=["*"],
            actions=["ses:SendEmail", "ses:SendRawEmail"],
        ))
        
        
        # Cron every 4 hours
        aws_events.Rule(
            scope=self,
            id=f'{project_id}-crawler-cron',
            schedule=aws_events.Schedule.rate(Duration.hours(4)),
            targets=[aws_events_targets.LambdaFunction(feed_extractor_lambda)]
        )
        
