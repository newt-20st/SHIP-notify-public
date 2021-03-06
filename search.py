import os
import json

from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

load_dotenv()

if not firebase_admin._apps:
    CREDENTIALS = credentials.Certificate({
    'type': 'service_account',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'project_id': os.environ['FIREBASE_PROJECT_ID'],
    'client_email': os.environ['FIREBASE_CLIENT_EMAIL'],
    'private_key': os.environ['FIREBASE_PRIVATE_KEY'].replace('\\n', '\n')
    })
    firebase_admin.initialize_app(CREDENTIALS,{'databaseURL': 'https://'+os.environ['FIREBASE_PROJECT_ID']+'.firebaseio.com'})
db = firestore.client()


def file(id):
    data = []
    docs = db.collection('highCon').where('id', '==', int(id)).stream()
    for doc in docs:
        eachDoc = doc.to_dict()
        data.append([eachDoc['title'], eachDoc['link'], eachDoc['date']])
    docs = db.collection('highStudy').where('id', '==', int(id)).stream()
    for doc in docs:
        eachDoc = doc.to_dict()
        data.append([eachDoc['title'], eachDoc['link'], eachDoc['date']])
    docs = db.collection('highSchoolNews').where('id', '==', int(id)).stream()
    for doc in docs:
        eachDoc = doc.to_dict()
        data.append([eachDoc['title'], eachDoc['link'], eachDoc['date']])
    return data


def info(id):
    data = []
    docs = db.collection('highCon').where('id', '==', int(id)).stream()
    for doc in docs:
        eachDoc = doc.to_dict()
        data.append([eachDoc['title'], eachDoc['date'], eachDoc['folder'], eachDoc['link'], "高校連絡事項", doc.id])
    docs = db.collection('highStudy').where('id', '==', int(id)).stream()
    for doc in docs:
        eachDoc = doc.to_dict()
        data.append([eachDoc['title'], eachDoc['date'], eachDoc['folder'], eachDoc['link'], "高校学習教材", doc.id])
    docs = db.collection('highSchoolNews').where('id', '==', int(id)).stream()
    for doc in docs:
        eachDoc = doc.to_dict()
        data.append([eachDoc['title'], eachDoc['date'], eachDoc['folder'], eachDoc['link'], "高校学校通信", doc.id])
    docs = db.collection('juniorCon').where('id', '==', int(id)).stream()
    for doc in docs:
        eachDoc = doc.to_dict()
        data.append([eachDoc['title'], eachDoc['date'], eachDoc['folder'], "", "中学連絡事項", doc.id])
    docs = db.collection('juniorStudy').where('id', '==', int(id)).stream()
    for doc in docs:
        eachDoc = doc.to_dict()
        data.append([eachDoc['title'], eachDoc['date'], eachDoc['folder'], "", "中学学習教材", doc.id])
    docs = db.collection('juniorSchoolNews').where('id', '==', int(id)).stream()
    for doc in docs:
        eachDoc = doc.to_dict()
        data.append([eachDoc['title'], eachDoc['date'], eachDoc['folder'], "", "中学学校通信", doc.id])
    return data


def recently(type, howmany):
    itemNameList = json.load(open('json/ship.json', 'r', encoding="utf-8_sig"))["pageList"]
    data = []
    docs = db.collection(itemNameList[type]["collectionName"]).order_by('id', direction=firestore.Query.DESCENDING).limit(int(howmany)).stream()
    for doc in docs:
        eachDoc = doc.to_dict()
        data.append({
            "title":  eachDoc['title'],
            "date": eachDoc['date'],
            "id": eachDoc['id']
        })
    return data


def count(type):
    itemNameList = json.load(open('json/ship.json', 'r', encoding="utf-8_sig"))["pageList"]
    dbc = db.collection('count')
    try:
        docDict = dbc.document(itemNameList[type]["collectionName"]).get().to_dict()
        return docDict['count']
    except Exception as e:
        return 0


if __name__ == "__main__":
    recently(5, 10)
