from aws_cdk import core, aws_lambda, aws_secretsmanager, aws_apigateway, aws_events, aws_events_targets
from stacks.stack_utils import *


class CrawlingStack(core.Stack):
    
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        """ Define Buckets """
        code_path = "./lambda/crawling"

        """ Define Layers """
        
        requests_layer = get_layer(self, "requests")
        pymongo_layer = get_layer(self, "pymongo")
        lxml_layer = get_layer(self, "lxml")
        feedparser_layer = get_layer(self, "feedparser")
        newspaper_layer = get_layer(self, "newspaper3k")

        secret = get_secret(self)
        
        """ Define Lambdas """
        
        #=====================================================
        # CLINICAL TRIALS
        #=====================================================
        article_lambda = get_lambda(
            scope=self,
            name="article_lambda",
            env_dict={
                "SECRET_ARN": secret.secret_arn,
            },
            layers=[pymongo_layer, newspaper_layer],
            code_path=code_path,
            reserved_concurrent_executions=5
        )

        feedparser_lambda = get_lambda(
            scope=self,
            name="feedparser_lambda",
            env_dict={
                "SECRET_ARN": secret.secret_arn,
                "ARTICLE_LAMBDA": article_lambda.function_name
            },
            layers=[pymongo_layer, feedparser_layer],
            code_path=code_path,
            reserved_concurrent_executions=5
        )

        feed_extractor_lambda = get_lambda(
            scope=self,
            name="feed_extractor_lambda",
            env_dict={
                "FEEDPARSER_LAMBDA": feedparser_lambda.function_name
            },
            layers=[lxml_layer, requests_layer],
            code_path=code_path
        )
        
        secret.grant_read(article_lambda)
        secret.grant_read(feedparser_lambda)
        secret.grant_read(feed_extractor_lambda)

        
        feedparser_lambda.grant_invoke(feed_extractor_lambda)
        article_lambda.grant_invoke(feedparser_lambda)
        

        # Cron every 2 hours
        aws_events.Rule(
            scope=self,
            id='crawler-cron',
            schedule=aws_events.Schedule.rate(core.Duration.hours(8)),
            targets=[aws_events_targets.LambdaFunction(feed_extractor_lambda)]
        )
        
