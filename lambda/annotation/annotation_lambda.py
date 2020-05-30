from pprint import pprint
import requests
from pymongo import MongoClient
import pymongo
import boto3
import json
import os
import time
from secrets import get_secret


secret_client = boto3.client("secretsmanager")
secrets = json.loads(secret_client.get_secret_value(SecretId=os.environ["SECRET_ARN"])["SecretString"])
#secrets = get_secret()

lambda_client = boto3.client("lambda")
db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]



def handler(event=None, context=None):

    # Deduplication on URL
    print("## Deduplicate URLs")
    i = 0
    for entry in db["articles"].aggregate([ { "$group": {"_id":"url" , "count":{"$sum":1}} }, {"$sort":{"count":-1}} ]):
        if entry["count"] > 1:
            ids_to_remove = db["articles"].find({"url": entry["_id"]}).distinct("_id")
            db["articles"].remove({"_id":{"$in":ids_to_remove}})
            i += len(ids_to_remove)
    print(f"{i} articles have been removed")


    # Deduplication on title + text
    print("## Deduplicate on Title + text")
    i = 0
    for entry in db["articles"].aggregate([ { "$group": {"_id":{"title":"$title", "source":"$meta.source.name", "text":"$text"} , "count":{"$sum":1}} }, {"$sort":{"count":-1}} ]):
        if entry["count"] > 1 and "text" in entry["_id"]:
            _ids = db["articles"].find({
                "title": entry["_id"]["title"],
                "meta.source.name": entry["_id"]["source"],
                "text": entry["_id"]["text"]
            }).distinct("_id")

            ids_to_remove = _ids[1:]
            db["articles"].remove({"_id":{"$in":ids_to_remove}})
            i += len(ids_to_remove)
    print(f"{i} articles have been removed")

    # TextRazor
    print("## Launch TextRazor")
    for i, article in enumerate(db["articles"].find({"text":{"$nin":[None, ""]}, "textrazor_response.ok":{"$exists":False}}, no_cursor_timeout=True).sort("date", pymongo.DESCENDING)):
        lambda_client.invoke(
            FunctionName=os.environ["TEXTRAZOR_LAMBDA"],
            InvocationType="Event",
            Payload=json.dumps({
                "mongo_id": str(article["_id"])
            })
        )
    print(f"{i} articles have been sent to TextRazor")

if __name__ == "__main__":
    handler()