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
    event = json.loads(event)
    url = event["url"]

    try:
        article = Article(url)
        article.download()
        article.parse()
    except:
        print(f"Error with the following url: {url}")
        return
    
    authors = article.authors
    date = article.publish_date
    text = article.text
    image = article.top_image
    summary = article.summary

    db["articles"].update_one({"url": url}, {"$set":{
        "date": date,
        "text": text,
        "meta.newspaper3k": {
            "authors": authors,
            "summary": summary,
            "top_image": image
        }
    }})

            

if __name__ == "__main__":
    handler(json.dumps({
        "url": "https://www.lecho.be/r/t/1/id/10228425"
    }))
    
