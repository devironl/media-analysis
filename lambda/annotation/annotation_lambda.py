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

    for article in db["articles"].find({"text":{"$nin":[None, ""]}, "textrazor_response.ok":{"$exists":False}}, no_cursor_timeout=True).sort("date", pymongo.DESCENDING).limit(6000):
              
        
        lambda_client.invoke(
            FunctionName=os.environ["TEXTRAZOR_LAMBDA"],
            InvocationType="Event",
            Payload=json.dumps({
                "mongo_id": str(article["_id"])
            })
        )

if __name__ == "__main__":
    handler()