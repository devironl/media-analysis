#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.CrawlingStack import CrawlingStack
from stacks.AnnotationStack import AnnotationStack

from config import account_id, region

aws_env = cdk.Environment(account=account_id, region=region)

app = cdk.App()
CrawlingStack(app, "media-analysis-crawling", env=aws_env)
AnnotationStack(app, "media-analysis-annotation", env=aws_env)

app.synth()
