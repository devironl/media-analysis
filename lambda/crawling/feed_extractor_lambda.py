import requests, re, json
from lxml import html
import boto3
import os
from reppy.robots import Robots
from secrets import get_secret
import random
from pymongo import MongoClient
import pymongo


secret_client = boto3.client("secretsmanager")

#secrets = get_secret()
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


def get_test_url(source):
    url = random.choice([elm["url"] for elm in db["articles"].find({"meta.source.name":source}).sort("_id", pymongo.DESCENDING).limit(100)])
    return url    


def handler(event=None, context=None):

    print(headers["User-Agent"])
    for source in ["rtbf.be", "lesoir.be", "lalibre.be", "dhnet.be", "sudinfo.be", "levif.be", "rtlinfo.be", "lavenir.net", "lecho.be"]:

        robots = Robots.fetch(f"http://www.{source}/robots.txt")
        
        agent = robots.agent(headers["User-Agent"])

        test_url = get_test_url(source)
        allowed = agent.allowed(test_url)
        
        try:
            feeds = get_feeds(source)
            print(f"{source}: {len(feeds)} detected")
        except:
            print(f"Error with following source: {source}")

        for feed in feeds:
            lambda_client.invoke(
                FunctionName=os.environ["FEEDPARSER_LAMBDA"],
                InvocationType="Event",
                Payload=json.dumps(feed)
            )

def get_feeds(source):

    feeds = []
    if source == "rtbf.be":
        return [{
            "name": source,
            "feed_url": "http://rss.rtbf.be/article/rss/rtbf_flux.xml",
            "feed_title": "Général",
            "country": "BE",
            "language": "fr"
        },{
            "name": source,
            "feed_url": "http://rss.rtbf.be/article/rss/highlight_rtbfinfo_info-accueil.xml",
            "feed_title": "Général",
            "country": "BE",
            "language": "fr"
        }]

    elif source == "lesoir.be":
        page = "https://plus.lesoir.be/services/rss"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for elm in root.xpath("//a[@class='rss__link']"):
            href = elm.get("href")
            if re.search("^/rss", href):
                feeds.append({
                    "name": source,
                    "feed_url": f"https://plus.lesoir.be{href}",
                    "feed_title": elm.text,
                    "country": "BE",
                    "language": "fr"
                })

    elif source in ["lalibre.be", "dhnet.be"]:
        page = f"https://www.{source}/rss/about"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath("//div[@id='rssLists']//tr"):
            url = rss.xpath(".//a[starts-with(@href, '/rss')]")[0]
            href = url.get("href")
            if re.search("^/rss", href):
                feeds.append({
                    "name": source,
                    "feed_url": f"https://{source}{href}",
                    "feed_title": " ".join(rss.xpath(".//td[@class='rubriqueName']//text()")).strip(),
                    "country": "BE",
                    "language": "fr"
                })
        
    elif source == "sudinfo.be":

        feeds = []
        page = "https://www.sudinfo.be/rss"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath("//li[@class='rss__item']//a"):
            feeds.append({
                "name": source,
                "feed_url": rss.get("href"),
                "feed_title": rss.text.strip(),
                "country": "BE",
                "language": "fr"
            })
    
    elif source == "levif.be":
        return [{
            "name": source,
            "feed_url": "https://www.levif.be/actualite/feed.rss",
            "feed_title": "Actualité",
            "country": "BE",
            "language": "fr"
        }, {
            "name": source,
            "feed_url":"https://trends.levif.be/economie/feed.rss",
            "feed_title": "Economie",
            "country": "BE",
            "language": "fr"
        }]

    elif source == "rtlinfo.be":
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
    
    elif source == "lavenir.net":
        page = "https://www.lavenir.net/extra/rss"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath(".//a[starts-with(@href, '/rss')]"):
            feeds.append({
                "name": source,
                "feed_url": f"https://lavenir.net{rss.get('href')}",
                "feed_title": "".join(rss.xpath(".//text()")[0].split("-")[:-1]).strip(),
                "country": "BE",
                "language": "fr"
            })
        
    elif source == "lecho.be":
        feeds = []
        page = "https://www.lecho.be/site2014/rss"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath(".//a[starts-with(@href, '/rss')]"):
            feeds.append({
                "name": source,
                "feed_url": f"https://lecho.be{rss.get('href')}",
                "feed_title": rss.text.strip(),
                "country": "BE",
                "language": "fr"
            })

    else:
        print(f"This source is not covered : {source}")
        
    return feeds


if __name__ == "__main__":
    handler()