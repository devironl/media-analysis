from secrets import get_secret
import pandas as pd

secrets = get_secret()
from pymongo import MongoClient
db = MongoClient(secrets["mongo_host"], username=secrets["mongo_user"], password=secrets["mongo_pwd"])["media_analysis"]

results = []

for entry in db["articles"].find():
    
    results.append({
        "source": entry["meta"]["source"]["name"],
        "date": entry["date"],
        "title": entry.get("title", None),
        "length": len(entry.get("text", "")),
        "language": entry["meta"]["source"]["language"]
    })

df = pd.DataFrame(results)
df.to_excel("./daily_stats.xlsx", index=False)

