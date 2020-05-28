import re, json
import boto3
import os
from pymongo import MongoClient
from secrets import get_secret
from newspaper import Article, fulltext
import random
import requests


def get_cookie(source):
    if source in ["hln.be", "demorgen.be"]:
        return "pwv=1; pws=functional"
        #return "pws=functional|analytics|content_recommendation|targeted_advertising|social_media; paywall_tracking_id=2cc04f17-9e0f-4bae-b8c0-a2a2f8525e4e; root_pwv_set=1; root_pws_set=1; _wingify_pc_uuid=78091bd4c75e45e8bcd1f7d43dc1d3bf; __gfp_64b=PGLWwAjPc3AVLKSjy2ml_1NyWA8YV6oSnD6c6rTrG2L.G7; gig_canary=false; _ga=GA1.2.1283091356.1589339835; cX_S=ka4rwijcn0nxfnj1; cX_P=ka4rwijhk9ysnnf7; gig_bootstrap_3_EqzvDtuTDxEfdBuDHV0-rMW3Ag4dgzOmN714tRjxGmFfjurkrbZMcWiO1-fyXt56=accounts_ver3; _sotmpid=0:ka4rwj5h:KuTUikqBN9UXqaL9pIVe4GJGbURjcoCh; cX_G=cx%3A18ie2wiy8kgq42m5hchkpczw7k%3A3ohqmox836oab; _gcl_au=1.1.809904153.1589339839; lastConsentChange=1590210312875; _hjid=0e44cfe1-0111-4ff4-8e27-e9b05876b251; OB-USER-TOKEN=a121b9f1-de85-4ad4-98ad-bd2981387b1a; _ain_uid=1590222867834.623282256.0777569; cstp=1; pwv=2; gig_canary_ver=11005-5-26510670; faktorIsInEU=true; _gid=GA1.2.802593160.1590641019; _sp_ses.5ba7=*; _sp_id.5ba7=5f502eab-1be3-49bb-8b55-aa5b988504b9.1589339836.8.1590641020.1590468976.240c96f8-1d02-4210-afff-99afb8c584ae; _gat_UA-187881-4=1; _sotmsid=0:kaqaletu:nMW822wpDN~XmB1q9IqAhfmtVkaaY7n4; gtm_session=1"
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

secrets = get_secret()
#secrets = json.loads(secret_client.get_secret_value(SecretId=os.environ["SECRET_ARN"])["SecretString"])

db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]

def handler(event=None, context=None):
    url = event["url"]
    source = event["source"]
    language = event["language"]

    print(url)

    cookie = get_cookie(source)


    article = Article(url, language=language)
    article.download()
    article.parse()
   
    if cookie is not None:
        headers["Cookie"] = cookie
       
        html = requests.get(url, headers=headers).text
        text = fulltext(html, language=language)

    else:
        text = article.text


    if "Websites hanteren" not in text and text != "":
        db["articles"].update_one({"url": url}, {"$set":{
            "text": text,
            "title": article.title,
            "meta.newspaper3k": {
                "authors": article.authors,
                "summary": article.summary,
                "top_image": article.top_image,
                "date": article.publish_date,
                "title": article.title
            }
        }})

def reprocess_empty_articles():
    urls = db["articles"].find({"meta.source.name":"lalibre.be", "text":{"$in":["", None]}}).distinct("url")
    random.shuffle(urls)
    print(len(urls))
    for i, url in enumerate(urls):
        if i % 10 == 0:
            print(i)
        handler({
            "url": url
        })
       
            
if __name__ == "__main__":
    url = "https://www.hln.be/in-de-buurt/lendelede/sofie-mag-maandag-milan-11-na-twee-maanden-ophalen-in-zorginstelling-neem-me-mee-mama-smeekt-hij-me-hij-denkt-telkens-dat-hij-gestraft-wordt-dan-breekt-je-hart~a486283b/"
    handler({"url":url, "source":"hln.be", "language":"nl"})

    #reprocess_empty_articles()
    