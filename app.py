#!/usr/bin/env python3

from aws_cdk import core

from stacks.CrawlingStack import CrawlingStack


app = core.App()
CrawlingStack(app, "media-analysis-crawling")

app.synth()
