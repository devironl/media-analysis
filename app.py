#!/usr/bin/env python3

from aws_cdk import core

from stacks.CrawlingStack import CrawlingStack
from stacks.AnnotationStack import AnnotationStack


app = core.App()
CrawlingStack(app, "media-analysis-crawling")
AnnotationStack(app, "media-analysis-annotation")

app.synth()
