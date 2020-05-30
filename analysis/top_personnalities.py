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

    title = article["title"]
    processed = set()
    
    for entity in article["textrazor_response"]["response"].get("entities", []):
        if True in [word in title for word in entity["matchedText"].split() if len(word) > 2]:
            if "Person" in entity.get("type", []) or "/people/person" in entity.get("freebaseTypes", []):
                
                if entity["entityId"] not in processed:
                    if "Magnette" in entity["matchedText"]:
                        i += 1
                    results.append({
                        "url": article["url"],
                        "title": article["title"],
                        "entity": entity["entityId"],
                        "date": article["date"].replace(tzinfo=None),
                        "language": article["meta"]["source"]["language"],
                        "source": article["meta"]["source"]["name"]
                    })
                    processed.add(entity["entityId"])
print(i)

df = pd.DataFrame(results)
df.to_excel(f"./result_files/{get_today_date()}_top_personnalities.xlsx", index=False)


