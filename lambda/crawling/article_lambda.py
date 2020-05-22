import re, json
import boto3
import os
from pymongo import MongoClient
from secrets import get_secret
from newspaper import Article

secret_client = boto3.client("secretsmanager")

#secrets = get_secret()
secrets = json.loads(secret_client.get_secret_value(SecretId=os.environ["SECRET_ARN"])["SecretString"])

db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]

def handler(event=None, context=None):
    url = event["url"]

    print(url)
    article = Article(url)
    article.download()
    article.parse()
    print(article.text)

    db["articles"].update_one({"url": url}, {"$set":{
        "date": article.publish_date,
        "text": article.text,
        "title": article.title,
        "meta.newspaper3k": {
            "authors": article.authors,
            "summary": article.summary,
            "top_image": article.top_image
        }
    }})

            
if __name__ == "__main__":
    handler({
        "url": "https://plus.lesoir.be/302007/article/2020-05-20/les-flamands-peu-seduits-par-leurs-politiques-durant-cette-crise"
    })
    
