import re, json
import boto3
import os
from pymongo import MongoClient
from secrets import get_secret
import feedparser
from datetime import datetime, timezone

lambda_client = boto3.client("lambda")
secret_client = boto3.client("secretsmanager")

#secrets = get_secret()
secrets = json.loads(secret_client.get_secret_value(SecretId=os.environ["SECRET_ARN"])["SecretString"])

db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]

def handler(event=None, context=None):
    feed_url = event["feed_url"]
    
    for article in feedparser.parse(feed_url)["entries"]:

        parsed_date = article.get("published_parsed", None)

        try:
            date = datetime(parsed_date[0], parsed_date[1], parsed_date[2], parsed_date[3], parsed_date[4], parsed_date[5], tzinfo=timezone.utc)
        except:
            date = None

        meta = {
            "title": article.get("title", None),
            "summary": article.get("summary", None),
            "published_parsed": date
        }
        
        to_crawl = False

        # if not already crawled
        if db["articles"].find_one({"url": article["link"]}) == None:
            
            # Inserts in DB
            db["articles"].insert_one({
                "url": article["link"],
                "date": date,
                "meta": {
                    "source": event,
                    "feedparser": meta
                }
            })
            
            # Crawling
            lambda_client.invoke(
                FunctionName=os.environ["ARTICLE_LAMBDA"],
                InvocationType="Event",
                Payload=json.dumps({"url": article["link"]})
            )
        
            

if __name__ == "__main__":
    handler({
        "feed_url": "https://lecho.be/rss/actualite.xml",
        "name": "lecho.be",
        "feed_title": "Actualité",
        "country": "BE",
        "language": "fr"
    })
    
