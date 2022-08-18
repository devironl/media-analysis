#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.CrawlingStack import CrawlingStack
from stacks.AnnotationStack import AnnotationStack


app = cdk.App()
CrawlingStack(app, "media-analysis-crawling")
AnnotationStack(app, "media-analysis-annotation")

app.synth()
