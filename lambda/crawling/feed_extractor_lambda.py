import requests, re, json
from lxml import html
import boto3
import os

lambda_client = boto3.client("lambda")


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ' 
    'AppleWebKit/537.11 (KHTML, like Gecko) '
    'Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'
}

def handler(event=None, context=None):

    for source in ["rtbf", "lesoir", "lalibre", "dhnet", "sudinfo", "levif", "rtlinfo", "lavenir", "lecho"]:

        feeds = get_feeds(source)
        print(f"{source}: {len(feeds)} detected")

   
        for feed in feeds:
            lambda_client.invoke(
                FunctionName=os.environ["FEEDPARSER_LAMBDA"],
                InvocationType="Event",
                Payload=json.dumps(feed)
            )



def get_feeds(source):

    feeds = []
    if source == "rtbf":
        return [{
            "source": "rtbf.be",
            "feed": "http://rss.rtbf.be/article/rss/rtbf_flux.xml",
            "title": "Général"
        }]

    elif source == "lesoir":
        page = "https://plus.lesoir.be/services/rss"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for elm in root.xpath("//a[@class='rss__link']"):
            href = elm.get("href")
            if re.search("^/rss", href):
                feeds.append({
                    "source": "lesoir.be",
                    "feed": f"https://plus.lesoir.be{href}",
                    "title": elm.text
                })

    elif source in ["lalibre", "dhnet"]:
        page = f"https://www.{source}.be/rss/about"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath("//div[@id='rssLists']//tr"):
            url = rss.xpath(".//a[starts-with(@href, '/rss')]")[0]
            href = url.get("href")
            if re.search("^/rss", href):
                feeds.append({
                    "source": f"{source}.be",
                    "feed": f"https://{source}.be{href}",
                    "title": " ".join(rss.xpath(".//td[@class='rubriqueName']//text()")).strip()
                })
        
    elif source == "sudinfo":

        feeds = []
        page = "https://www.sudinfo.be/rss"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath("//li[@class='rss__item']//a"):
            feeds.append({
                "source": "sudinfo.be",
                "feed": rss.get("href"),
                "title": rss.text.strip()
            })
    
    elif source == "levif":
        return [{
            "source": "levif.be",
            "feed": "https://www.levif.be/actualite/feed.rss",
            "title": "Actualité"
        }, {
            "source": "levif.be",
            "feed":"https://trends.levif.be/economie/feed.rss",
            "title": "Economie"
        }]

    elif source == "rtlinfo":
        page = "https://www.rtl.be/info/page/flux-rss-rtl-be/650.aspx"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath(".//a[starts-with(@href, '//feeds')]"):
        
            feeds.append({
                "source": "rtlinfo.be",
                "feed": f"https:{rss.get('href')}",
                "title": rss.get("href").split("/")[-1].strip()
            })
    
    elif source == "lavenir":
        page = "https://www.lavenir.net/extra/rss"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath(".//a[starts-with(@href, '/rss')]"):
            feeds.append({
                "source": "lavenir.net",
                "feed": f"https://lavenir.net{rss.get('href')}",
                "title": "".join(rss.xpath(".//text()")[0].split("-")[:-1]).strip()
            })
        
    elif source == "lecho":
        feeds = []
        page = "https://www.lecho.be/site2014/rss"
        r = requests.get(page, headers=headers)
        root = html.fromstring(r.text)
        for rss in root.xpath(".//a[starts-with(@href, '/rss')]"):
            feeds.append({
                "source": "lecho.be",
                "feed": f"https://lecho.be{rss.get('href')}",
                "title": rss.text.strip()
            })

    else:
        print(f"This source is not covered : {source}")
        
    return feeds


if __name__ == "__main__":
    handler()