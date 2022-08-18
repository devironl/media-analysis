from constructs import Construct
from aws_cdk import Stack, Duration
from aws_cdk import aws_lambda
from aws_cdk import aws_secretsmanager
from aws_cdk import aws_apigateway
from aws_cdk import aws_events, aws_events_targets


class CrawlingStack(Stack):
    
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        code_path = "./lambda/crawling"

        secret = aws_secretsmanager.Secret.from_secret_attributes(
            scope=self,
            id="media-analysis-secret",
            secret_partial_arn=f"arn:aws:secretsmanager:eu-west-3:771823009556:secret:media_analysis_secret"
        )
        
        """ Define Lambdas """
        
        # Crawl article
        article_lambda = PythonFunction(
            scope=self,
            id=f"media-analysis-article-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            function_name=f"media-analysis-article-lambda",
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
            id=f"media-analysis-feedparser-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            function_name=f"media-analysis-feedparser-lambda",
            entry=code_path,
            index="feedparser_lambda.py",
            environment={
                "SECRET_ARN": secret.secret_arn,
                "ARTICLE_LAMBDA": article_lambda.function_name
            },
            timeout=Duration.seconds(900),
            memory_size=3008,
            reserved_concurrent_executions=10
        )
      

        # Extract RSS feeds
        feed_extractor_lambda = PythonFunction(
            scope=self,
            id=f"media-analysis-feed-extractor-lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            function_name=f"media-analysis-feed-extractor-lambda",
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
        
        # Cron every 4 hours
        aws_events.Rule(
            scope=self,
            id='media-analysis-crawler-cron',
            schedule=aws_events.Schedule.rate(Duration.hours(4)),
            targets=[aws_events_targets.LambdaFunction(feed_extractor_lambda)]
        )
        
