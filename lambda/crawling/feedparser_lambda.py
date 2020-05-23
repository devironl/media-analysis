import re, json
import boto3
import os
from pymongo import MongoClient
from secrets import get_secret
import feedparser
from datetime import datetime, timezone
from pprint import pprint
from xml.etree import ElementTree
from io import StringIO 
from dateutil import parser

import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'
}

lambda_client = boto3.client("lambda")
secret_client = boto3.client("secretsmanager")

#secrets = get_secret()
secrets = json.loads(secret_client.get_secret_value(SecretId=os.environ["SECRET_ARN"])["SecretString"])

db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]

def handler(event=None, context=None):
    feed_url = event["feed_url"]
    feedparser.USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
    
    feed = feedparser.parse(feed_url).get("entries", [])
    articles = []
    
    ## FEEDPARSER
    if len(feed) > 0:
    
        for article in feed:

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

            articles.append({
                "url": article["link"],
                "date": date,
                "title": article.get("title", None),
                "meta": {
                    "source": event,
                    "feedparser": meta
                }
            })

    ## GOOGLE NEWS SITEMAP
    elif "google" in feed_url:
        r = requests.get(feed_url, headers=headers).text
        
        # instead of ET.fromstring(xml)
        tree = ElementTree.iterparse(StringIO(r))
        tree = remove_namespaces(tree)

        root = tree.root
        for entry in root.findall("url"):
            url = entry.find("loc")
            if url is not None:
                url = url.text
                title = entry.find("news").find("title").text
                publication_date = entry.find("news").find("publication_date").text
                publication_date = parser.parse(publication_date)
                try:
                    keywords = entry.find("news").find("keywords").text
                except:
                    keywords = ""

                articles.append({
                    "url": url,
                    "title": title,
                    "date": publication_date,
                    "meta": {
                        "source": event,
                        "feedparser": {
                            "title": title,
                            "published_parse": publication_date,
                            "keywords": keywords
                        }
                    }
                })

    for article in articles:
        # if not already crawled
        if db["articles"].find_one({"url": article["url"]}) == None:
            
            # Inserts in DB
            db["articles"].insert_one(article)
            
            # Crawling
            lambda_client.invoke(
                FunctionName=os.environ["ARTICLE_LAMBDA"],
                InvocationType="Event",
                Payload=json.dumps({"url": article["url"]})
            )

def remove_namespaces(tree):
    for _, el in tree:
        for _, el in tree:
            _, _, el.tag = el.tag.rpartition('}')
    return tree


if __name__ == "__main__":
    handler({
       # "feed_url": "https://www.hln.be/google-news.xml",
        "feed_url":"https://www.lalibre.be/sitemap_googlenews.xml",
        "name": "hln.be",
        "feed_title": "Actualité",
        "country": "BE",
        "language": "nl"
    })
    
