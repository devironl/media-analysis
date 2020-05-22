import re, json
import boto3
import os
from pymongo import MongoClient
from secrets import get_secret
from newspaper import Article
import random


secret_client = boto3.client("secretsmanager")

#secrets = get_secret()
secrets = json.loads(secret_client.get_secret_value(SecretId=os.environ["SECRET_ARN"])["SecretString"])

db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]

def handler(event=None, context=None):
    url = event["url"]

    article = Article(url)
    article.download()
    article.parse()

    db["articles"].update_one({"url": url}, {"$set":{
        "text": article.text,
        "title": article.title,
        "meta.newspaper3k": {
            "authors": article.authors,
            "summary": article.summary,
            "top_image": article.top_image,
            "date": article.publish_date
        }
    }})

def reprocess_empty_articles():
    urls = db["articles"].find({"text":{"$in":["", None]}}).distinct("url")
    random.shuffle(urls)
    print(len(urls))
    for i, url in enumerate(urls):
        if i % 10 == 0:
            print(i)
        try:
            handler({
                "url": url
            })
        except:
            pass
            
if __name__ == "__main__":

    reprocess_empty_articles()

