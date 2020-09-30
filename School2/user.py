import pandas as pd
import pymongo

client = pymongo.MongoClient(
    "mongodb+srv://g0utham:Sg106271@cluster0-v0h6w.gcp.mongodb.net/?retryWrites=true&w=majority"
)
db = client.school_manage

users=pd.read_csv('School2/users.csv')
print(users)