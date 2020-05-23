import re, json
import boto3
import os
from pymongo import MongoClient
from secrets import get_secret
from newspaper import Article, fulltext
import random
import requests

def get_cookie(url):
    if "hln.be" in url or "demorgen.be" in url:
        return "pwv=1; pws=functional"
    
    return None


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive',
}

secret_client = boto3.client("secretsmanager")

#secrets = get_secret()
secrets = json.loads(secret_client.get_secret_value(SecretId=os.environ["SECRET_ARN"])["SecretString"])

db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]

def handler(event=None, context=None):
    url = event["url"]

    cookie = get_cookie(url)
    if cookie is not None:
        headers["Cookie"] = cookie
       
        html = requests.get(url, headers=headers).text
      
        
        db["articles"].update_one({"url": url}, {"$set": {
            "text": text
        }})
   
    else:
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
    