from pprint import pprint
import requests
from pymongo import MongoClient
import boto3
import json
import os
from bson import ObjectId
from secrets import get_secret
import unicodedata 



secret_client = boto3.client("secretsmanager")
secrets = json.loads(secret_client.get_secret_value(SecretId=os.environ["SECRET_ARN"])["SecretString"])
#secrets = get_secret()
db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]

def get_language_code(lang):
    if lang == "fr":
        return "fre"
    elif lang == "nl":
        return "dut"

def get_best_title(article):
    titles = [article.get("title"), article["meta"].get("newspaper3k", {}).get("title", None), article["meta"].get("feedparser", {}).get("title", None)]
    titles = set([unicodedata.normalize("NFKD", title) for title in titles if title is not None])
    if len(titles) == 1:
        return list(titles)[0]
    return max(titles, key=len)


def handler(event, context=None):

    mongo_id = ObjectId(event["mongo_id"])
    
    article = db["articles"].find_one({"_id":mongo_id, "text":{"$nin":[None,""]}})

    if article == None:
        print("ERROR : empty content")
        return "Empty content"

    if article.get("textrazor_response", {}).get("ok", False) == True:
        print("ERROR : already processed")
        return "Already processed"

    best_title = get_best_title(article)
    
    textrazor_response = requests.post(
        "https://api.textrazor.com",
        data={
            "extractors":"entities,topics",
            "text": best_title + "\n" + article["text"],
            "languageOverride": get_language_code(article["meta"]["source"]["language"])
        },
        headers={
            "x-textrazor-key": secrets["textrazor_api_key"]
        }
    )
    if textrazor_response.status_code != 200:
        print("ERROR :", textrazor_response.status_code)
        return "Error :", textrazor_response.status_code

    textrazor_response = textrazor_response.json()
    db["articles"].update_one({"_id": mongo_id}, {"$set": {"textrazor_response":textrazor_response, "title": best_title}})
    
   
if __name__ == "__main__":

    for article in db["articles"].aggregate([{"$sample":{"size":10}}]):
        handler({"mongo_id": str(article["_id"])})