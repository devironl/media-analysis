from secrets import get_secret
from pprint import pprint
from pymongo import MongoClient
from datetime import datetime
import pandas as pd

secrets = get_secret()

db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]

def get_today_date():
    today = datetime.now()
    return datetime.strftime(today, "%Y%m%d")

results = []
i = 0
for article in db["articles"].find({"textrazor_response.ok":True, "date":{"$gte":datetime(2020,5,22)}}, no_cursor_timeout=True):

    topics = article["textrazor_response"]["response"].get("coarseTopics", [])
    if len(topics) > 0:
        topic = topics[0]["label"]

        results.append({
            "url": article["url"],
            "title": article["title"],
            "topic": topics[0]["label"],
            "date": article["date"].replace(tzinfo=None),
            "language": article["meta"]["source"]["language"],
            "source": article["meta"]["source"]["name"]
        })
        

df = pd.DataFrame(results)
df.to_excel(f"./result_files/{get_today_date()}_top_topics.xlsx", index=False)


