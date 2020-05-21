import re, json
import boto3
import os
from pymongo import MongoClient
from secrets import get_secret
import feedparser


lambda_client = boto3.client("lambda")
secret_client = boto3.client("secretsmanager")

#secrets = get_secret()
secrets = json.loads(secret_client.get_secret_value(SecretId=os.environ["SECRET_ARN"])["SecretString"])

db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]

def handler(event=None, context=None):
    event = json.loads(event)
    feed_url = event["feed"]
    
    for article in feedparser.parse(feed_url)["entries"]:

        for field in ["summary_detail", "title_detail", "tags", "links", "id", "guidislink"]:
            try:
                del article[field]
            except:
                pass

        # if not already crawled
        if db["articles"].find_one({"url": article["link"]}) == None:
            # Inserts in DB
            db["articles"].insert_one({
                "url": article["link"],
                "meta": {
                    "source": event,
                    "feedparser": article
                }
            })

            
            # Crawling
            lambda_client.invoke(
                FunctionName=os.environ["ARTICLE_LAMBDA"],
                InvocationType="Event",
                Payload=json.dumps({"url": article["link"]})
            )
            

if __name__ == "__main__":
    handler(json.dumps({
        "feed": "https://lecho.be/rss/actualite.xml",
        "source": "lecho.be",
        "title": "Actualité"
    }))
    
