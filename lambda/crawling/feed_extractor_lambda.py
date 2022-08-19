import requests, re, json
from lxml import html
import boto3
import os
import random
from pymongo import MongoClient
import pymongo
import pandas as pd


secret_client = boto3.client("secretsmanager")

secrets = json.loads(secret_client.get_secret_value(SecretId=os.environ["SECRET_ARN"])["SecretString"])
db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]


lambda_client = boto3.client("lambda")

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'
}

#be_fr_sources = ["rtbf.be", "rtlinfo.be", "sudinfo.be", "lavenir.net", "lesoir.be", "dhnet.be", "lalibre.be", "lecho.be", "levif.be"]
#be_nl_sources = ["vrt.be", "hln.be", "nieuwsblad.be", "hbvl.be", "gva.be", "standaard.be", "demorgen.be", "tijd.be", "knack.be"]

def handler(event=None, context=None):

    # Sitemap feeds
    df = pd.read_csv("./sources/sources.csv")
    for feed in df.to_dict("records"):
        lambda_client.invoke(
            FunctionName=os.environ["FEEDPARSER_LAMBDA"],
            InvocationType="Event",
            Payload=json.dumps(feed)
        )
    
    # RSS Feeds
    for source in ["rtlinfo.be", "gva.be", "standaard.be", "nieuwsblad.be", "hbvl.be"]:
        for feed in get_feeds(source):
            lambda_client.invoke(
            FunctionName=os.environ["FEEDPARSER_LAMBDA"],
            InvocationType="Event",
            Payload=json.dumps(feed)
        )
    
        
            
        
def get_feeds(source):

    feeds = []        
    
    if source == "rtlinfo.be":
       
        page = "https://www.rtl.be/info/page/flux-rss-rtl-be/650.aspx"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath(".//a[starts-with(@href, '//feeds')]"):
        
            feeds.append({
                "name": source,
                "feed_url": f"https:{rss.get('href')}",
                "feed_title": rss.get("href").split("/")[-1].strip(),
                "country": "BE",
                "language": "fr"
            })
    
    
    elif source == "standaard.be":
        page = "https://www.standaard.be/rssfeeds"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath(".//a[starts-with(@href, '/rss/')]"):
            feeds.append({
                "name": source,
                "feed_url": f"https://standaard.be{rss.get('href')}",
                "feed_title": rss.text.replace("\xa0", "").replace(">", "").strip(),
                "country": "BE",
                "language": "nl"
            })

    elif source == "demorgen.be":
        for title, url in {
            "In het nieuws" : "https://www.demorgen.be/in-het-nieuws/rss.xml",
            "Meningen": "https://www.demorgen.be/meningen/rss.xml",
            "Politiek": "https://www.demorgen.be/politiek/rss.xml",
            "TV & Cultuur": "https://www.demorgen.be/tv-cultuur/rss.xml",
            "Voor u uitgelegd": "https://www.demorgen.be/voor-u-uitgelegd/rss.xml",
            "Tech & wetenschap": "https://www.demorgen.be/tech-wetenschap/rss.xml",
            "Leven & Liefde": "https://www.demorgen.be/leven-liefde/rss.xml",
            "Sport": "https://www.demorgen.be/sport/rss.xml"
        }.items():
            feeds.append({
                "name": source,
                "feed_url": url,
                "feed_title": title, 
                "country": "BE",
                "language": "nl"
            })

    elif source in ["gva.be", "hbvl.be"]:
        page = f"https://www.{source}/rss"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath(f".//a[starts-with(@href, '//www.{source}/rss/')]"):
            if rss.text is not None:
                feeds.append({
                    "name": source,
                    "feed_url": f"https:{rss.get('href')}",
                    "feed_title": rss.text.strip(),
                    "country": "BE",
                    "language": "nl"
                })
    
    elif source == "nieuwsblad.be":
        page = f"https://www.nieuwsblad.be/rss"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath(f".//a[contains(@href, '/rss/')]"):
            feeds.append({
                "name": source,
                "feed_url": rss.get('href'),
                "feed_title": rss.text.strip(),
                "country": "BE",
                "language": "nl"
            })
       

        
    
    else:
        print(f"This source is not covered : {source}")
        
    return feeds
    