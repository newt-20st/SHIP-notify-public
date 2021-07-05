import datetime
import os
import random
import re
import time

from dotenv import load_dotenv
import pyrebase
from bs4 import BeautifulSoup
from selenium import webdriver
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

load_dotenv()

DATABASE_URL = os.environ['DATABASE_URL']

config = {
    'apiKey': os.environ['FIREBASE_API_KEY'],
    'authDomain': os.environ['FIREBASE_AUTH_DOMAIN'],
    "databaseURL": "xxxxxx",
    'storageBucket': os.environ['FIREBASE_STORAGE_BUCKET']
}
firebase = pyrebase.initialize_app(config)


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

def main():
    now = datetime.datetime.now()
    getTime = now.strftime('%H:%M:%S')

    gotList = []
    try:
        docs = db.collection('juniorCon').stream()
        gotList.extend([int(doc.to_dict()['id']) for doc in docs])
    except Exception as e:
        print(str(e))
    try:
        docs = db.collection('juniorStudy').stream()
        gotList.extend([int(doc.to_dict()['id']) for doc in docs])
    except Exception as e:
        print(str(e))
    try:
        docs = db.collection('juniorSchoolNews').stream()
        gotList.extend([int(doc.to_dict()['id']) for doc in docs])
    except Exception as e:
        print(str(e))
    try:
        docs = db.collection('highCon').stream()
        gotList.extend([int(doc.to_dict()['id']) for doc in docs])
    except Exception as e:
        print(str(e))
    try:
        docs = db.collection('highStudy').stream()
        gotList.extend([int(doc.to_dict()['id']) for doc in docs])
    except Exception as e:
        print(str(e))
    try:
        docs = db.collection('highSchoolNews').stream()
        gotList.extend([int(doc.to_dict()['id']) for doc in docs])
    except Exception as e:
        print(str(e))

    if os.environ['STATUS'] == "local":
        CHROME_DRIVER_PATH = 'C:\chromedriver.exe'
        DOWNLOAD_DIR = 'D:\Downloads'
    else:
        CHROME_DRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
        DOWNLOAD_DIR = '/app/tmp'
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument('start-maximized')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    prefs = {'download.default_directory': DOWNLOAD_DIR,'download.prompt_for_download': False}
    options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH,options=options)
    driver.command_executor._commands['send_command'] = ('POST','/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior','params': {'behavior': 'allow','downloadPath': DOWNLOAD_DIR}}
    driver.execute('send_command', params)
    driver.get('https://ship.sakae-higashi.jp/')
    ship_id = driver.find_element_by_name("ship_id")
    password = driver.find_element_by_name("pass")
    ship_id.send_keys(os.environ['SHIP_ID'])
    password.send_keys(os.environ['SHIP_PASS'])
    driver.find_element_by_name('login').click()
    time.sleep(1)
    count = 0
    while count < 2:
        if count == 0:
            schooltype = "high"
        elif count == 1:
            schooltype = "junior"
        driver.get("https://ship.sakae-higashi.jp/menu.php")
        menu = driver.page_source
        menuSoup = BeautifulSoup(menu, 'html.parser')
        menuStatus = menuSoup.find_all('table')[1].text
        if schooltype == "high" and '中学校' in menuStatus:
            driver.find_element_by_name('cheng_hi').click()
        elif schooltype == "junior" and '高等学校' in menuStatus:
            driver.find_element_by_name('cheng_jr').click()
        driver.get(
            "https://ship.sakae-higashi.jp/connection/search.php?obj_id=&depth=&search=&s_y=2011&s_m=01&s_d=01&e_y=2030&e_m=12&e_d=31")
        con = driver.page_source
        conSoup = BeautifulSoup(con, 'html.parser')
        conTrs = conSoup.find_all(class_='allc')[0].find_all('tr')
        conTrs.pop(0)
        conList = []
        for conTr in conTrs:
            time.sleep(1)
            eachconList = {}
            conTrTds = conTr.find_all('td')
            try:
                stage = conTrTds[2].find('a').get('onclick')
                conId = re.findall("'([^']*)'", stage)
                if int(conId[0]) not in gotList:
                    try:
                        eachconList["id"] = conId
                        driver.get(
                            "https://ship.sakae-higashi.jp/sub_window_anke/?obj_id="+conId[0]+"&t=3")
                        conEachPageSoup = BeautifulSoup(
                            driver.page_source, 'html.parser')
                        conPageMain = conEachPageSoup.find_all(class_='ac')[0].find_all(class_='bg_w')[0]
                        conPageDescription = conPageMain.find_all(
                            "table")[-2].text.replace("\n", "")
                        eachconList["description"] = conPageDescription
                        if schooltype == "high":
                            conPageLinks = conPageMain.find_all("a")
                            conPageLinkList = []
                            for eachConPageLink in conPageLinks:
                                driver.get("https://ship.sakae-higashi.jp" + eachConPageLink.get("href"))
                                result = re.match(".*name=(.*)&size.*", eachConPageLink.get("href"))
                                print(result.group(1))
                                time.sleep(5)
                                if os.environ['STATUS'] == "local":
                                    filepath = 'D:\Downloads/' + result.group(1)
                                else:
                                    filepath = DOWNLOAD_DIR + '/' + result.group(1)
                                storage = firebase.storage()
                                try:
                                    storage.child(
                                        'pdf/high-con/'+str(eachconList[0][0])+'/'+result.group(1)).put(filepath)
                                    conPageLinkList.append(storage.child(
                                        'pdf/high-con/'+str(eachconList[0][0])+'/'+result.group(1)).get_url(token=None))
                                except Exception as e:
                                    print(str(e))
                            eachconList["link"] = conPageLinkList
                    except Exception as e:
                        print(str(e))
                        eachconList["id"] = [0, 0]
                        eachconList["description"] = ""
                    eachconList["date"] = conTrTds[0].text
                    try:
                        eachconList["folder"] = conTrTds[1].find('span').get('title')
                    except:
                        eachconList["folder"] = ""
                    eachconList["title"] = conTrTds[2].text.replace("\n", "")
                    conList.append(eachconList)
            except Exception as e:
                print(str(e))
        print(conList)

        driver.get(
            "https://ship.sakae-higashi.jp/study/search.php?obj_id=&depth=&search=&s_y=2011&s_m=01&s_d=01&e_y=2030&e_m=12&e_d=31")
        study = driver.page_source
        studySoup = BeautifulSoup(study, 'html.parser')
        studyTrs = studySoup.find_all(class_='allc')[0].find_all('tr')
        studyTrs.pop(0)
        studyList = []
        for studyTr in studyTrs:
            time.sleep(1)
            eachstudyList = {}
            studyTrTds = studyTr.find_all('td')
            try:
                stage = studyTrTds[2].find('a').get('onclick')
                studyId = re.findall("'([^']*)'", stage)
                if int(studyId[0]) not in gotList:
                    try:
                        eachstudyList["id"] = studyId
                        driver.get(
                            "https://ship.sakae-higashi.jp/sub_window_study/?obj_id="+studyId[0]+"&t=7")
                        studyEachPageSoup = BeautifulSoup(
                            driver.page_source, 'html.parser')
                        if schooltype == "high":
                            try:
                                studyPageMain = studyEachPageSoup.find_all(
                                    class_='ac')[0].find_all("table")[1]
                                studyPageLinks = studyPageMain.find_all(
                                    "table")[-1].find_all("a")
                            except Exception as e:
                                print(str(e))
                            studyPageLinkList = []
                            for eachstudyPageLink in studyPageLinks:
                                driver.get("https://ship.sakae-higashi.jp" + eachstudyPageLink.get("href"))
                                result = re.match(".*name=(.*)&size.*", eachstudyPageLink.get("href"))
                                print(result.group(1))
                                time.sleep(4)
                                if os.environ['STATUS'] == "local":
                                    filepath = 'D:\Downloads/' + result.group(1)
                                else:
                                    filepath = DOWNLOAD_DIR + '/' + result.group(1)
                                storage = firebase.storage()
                                try:
                                    storage.child(
                                        'pdf/high-study/'+str(eachstudyList[0][0])+'/'+result.group(1)).put(filepath)
                                    studyPageLinkList.append(storage.child(
                                        'pdf/high-study/'+str(eachstudyList[0][0])+'/'+result.group(1)).get_url(token=None))
                                except Exception as e:
                                    print(str(e))
                            eachstudyList["link"] = studyPageLinkList
                    except Exception as e:
                        print(str(e))
                        eachstudyList["id"] = [0, 0]
                    eachstudyList["date"] = studyTrTds[0].text
                    try:
                        eachstudyList["folder"] = studyTrTds[1].find('span').get('title')
                    except:
                        eachstudyList["folder"] = ""
                    try:
                        eachstudyList["title"] = studyTrTds[2].text.replace("\n", "")
                    except:
                        eachstudyList["title"] = ""
                    studyList.append(eachstudyList)
            except Exception as e:
                print(str(e))
        print(studyList)

        driver.get(
            "https://ship.sakae-higashi.jp/school_news/search.php?obj_id=&depth=&search=&s_y=2011&s_m=01&s_d=01&e_y=2030&e_m=12&e_d=31")
        schoolNews = driver.page_source
        schoolNewsSoup = BeautifulSoup(schoolNews, 'html.parser')
        schoolNewsTrs = schoolNewsSoup.find_all(class_='allc')[0].find_all('tr')
        schoolNewsTrs.pop(0)
        schoolNewsList = []
        for schoolNewsTr in schoolNewsTrs:
            time.sleep(1)
            eachSchoolNewsList = {}
            schoolNewsTrTds = schoolNewsTr.find_all('td')
            try:
                stage = schoolNewsTrTds[2].find('a').get('onclick')
                schoolNewsId = re.findall("'([^']*)'", stage)
                if int(schoolNewsId[0]) not in gotList:
                    try:
                        eachSchoolNewsList["id"] = schoolNewsId
                        driver.get(
                            "https://ship.sakae-higashi.jp/sub_window/?obj_id="+schoolNewsId[0]+"&t=4")
                        schoolNewsEachPageSoup = BeautifulSoup(
                            driver.page_source, 'html.parser')
                        schoolNewsPageMain = schoolNewsEachPageSoup.find_all(class_='ac')[0].find_all(class_='bg_w')[0]
                        schoolNewsPageDescription = schoolNewsPageMain.find_all(
                            "table")[-2].text.replace("\n", "")
                        eachSchoolNewsList["description"] = schoolNewsPageDescription
                        if schooltype == "high":
                            schoolNewsPageLinks = schoolNewsPageMain.find_all("a")
                            schoolNewsPageLinkList = []
                            for eachSchoolNewsPageLink in schoolNewsPageLinks:
                                driver.get("https://ship.sakae-higashi.jp" + eachSchoolNewsPageLink.get("href"))
                                result = re.match(".*name=(.*)&size.*", eachSchoolNewsPageLink.get("href"))
                                time.sleep(5)
                                if os.environ['STATUS'] == "local":
                                    filepath = 'D:\Downloads/' + result.group(1)
                                else:
                                    filepath = DOWNLOAD_DIR + '/' + result.group(1)
                                storage = firebase.storage()
                                try:
                                    storage.child(
                                        'pdf/high-schoolNews/'+str(eachSchoolNewsList[0][0])+'/'+result.group(1)).put(filepath)
                                    schoolNewsPageLinkList.append(storage.child(
                                        'pdf/high-schoolNews/'+str(eachSchoolNewsList[0][0])+'/'+result.group(1)).get_url(token=None))
                                except Exception as e:
                                    print(str(e))
                            eachSchoolNewsList["link"] = schoolNewsPageLinkList
                    except Exception as e:
                        print(str(e))
                        eachSchoolNewsList["id"] = [0, 0]
                        eachSchoolNewsList["description"] = ""
                    eachSchoolNewsList["date"] = schoolNewsTrTds[0].text
                    try:
                        eachSchoolNewsList["folder"] = schoolNewsTrTds[1].find('span').get('title')
                    except:
                        eachSchoolNewsList["folder"] = ""
                    eachSchoolNewsList["title"] = schoolNewsTrTds[2].text.replace("\n", "")
                    schoolNewsList.append(eachSchoolNewsList)
            except Exception as e:
                print(str(e))
        print(schoolNewsList)

        if schooltype == "junior":
            juniorConList = conList
            juniorStudyList = studyList
            juniorSchoolNewsList = schoolNewsList
        elif schooltype == "high":
            highConList = conList
            highStudyList = studyList
            highSchoolNewsList = schoolNewsList
        count += 1
    driver.quit()

    juniorConSendData = []
    for i in reversed(juniorConList):
        if i["id"][0] != 0 and i["id"][0] not in gotList:
            i["date"] = i["date"].replace("年", "/").replace("月", "/").replace("日", "")
            juniorConSendData.append(i)
            db.collection('juniorCon').add({
                'id': int(i["id"][0]),
                'date': i["date"],
                'folder': i["folder"],
                'title': i["title"],
                'description': i["description"],
                'timestamp': firestore.SERVER_TIMESTAMP
            })
    docDict = db.collection('count').document('juniorCon').get().to_dict()
    if len(juniorConSendData) != 0:
        howManyData = int(docDict['count']) + len(juniorConSendData)
        db.collection('count').document('juniorCon').update({'count': howManyData, 'update': firestore.SERVER_TIMESTAMP})
    
    juniorStudySendData = []
    for i in reversed(juniorStudyList):
        if i["id"][0] != 0 and i["id"][0] not in gotList:
            i["date"] = i["date"].replace("年", "/").replace("月", "/").replace("日", "")
            juniorStudySendData.append(i)
            db.collection('juniorStudy').add({
                'id': int(i["id"][0]),
                'date': i["date"],
                'folder': i["folder"],
                'title': i["title"],
                'timestamp': firestore.SERVER_TIMESTAMP
            })
    docDict = db.collection('count').document('juniorStudy').get().to_dict()
    if len(juniorStudySendData) != 0:
        howManyData = int(docDict['count']) + len(juniorStudySendData)
        db.collection('count').document('juniorStudy').update({'count': howManyData, 'update': firestore.SERVER_TIMESTAMP})
    
    juniorSchoolNewsSendData = []
    for i in reversed(juniorSchoolNewsList):
        if i["id"][0] != 0 and i["id"][0] not in gotList:
            i["date"] = i["date"].replace("年", "/").replace("月", "/").replace("日", "")
            juniorSchoolNewsSendData.append(i)
            db.collection('juniorSchoolNews').add({
                'id': int(i["id"][0]),
                'date': i["date"],
                'folder': i["folder"],
                'title': i["title"],
                'timestamp': firestore.SERVER_TIMESTAMP
            })
    docDict = db.collection('count').document('juniorSchoolNews').get().to_dict()
    if len(juniorSchoolNewsSendData) != 0:
        howManyData = int(docDict['count']) + len(juniorSchoolNewsSendData)
        db.collection('count').document('juniorSchoolNews').update({'count': howManyData, 'update': firestore.SERVER_TIMESTAMP})
    
    highConSendData = []
    for i in reversed(highConList):
        if i["id"][0] != 0 and i["id"][0] not in gotList:
            i["date"] = i["date"].replace("年", "/").replace("月", "/").replace("日", "")
            highConSendData.append(i)
            db.collection('highCon').add({
                'id': int(i["id"][0]),
                'date': i["date"],
                'folder': i["folder"],
                'title': i["title"],
                'description': i["description"],
                'link': i["link"],
                'timestamp': firestore.SERVER_TIMESTAMP
            })
    docDict = db.collection('count').document('highCon').get().to_dict()
    if len(highConSendData) != 0:
        howManyData = int(docDict['count']) + len(highConSendData)
        db.collection('count').document('highCon').update({'count': howManyData, 'update': firestore.SERVER_TIMESTAMP})
    
    highStudySendData = []
    for i in reversed(highStudyList):
        if i["id"][0] != 0 and i["id"][0] not in gotList:
            i["date"] = i["date"].replace("年", "/").replace("月", "/").replace("日", "")
            highStudySendData.append(i)
            db.collection('highStudy').add({
                'id': int(i["id"][0]),
                'date': i["date"],
                'folder': i["folder"],
                'title': i["title"],
                'link': i["link"],
                'timestamp': firestore.SERVER_TIMESTAMP
            })
    docDict = db.collection('count').document('highStudy').get().to_dict()
    if len(highStudySendData) != 0:
        howManyData = int(docDict['count']) + len(highStudySendData)
        db.collection('count').document('highStudy').update({'count': howManyData, 'update': firestore.SERVER_TIMESTAMP})
    
    highSchoolNewsSendData = []
    for i in reversed(highSchoolNewsList):
        if i["id"][0] != 0 and i["id"][0] not in gotList:
            i["date"] = i["date"].replace("年", "/").replace("月", "/").replace("日", "")
            highSchoolNewsSendData.append(i)
            db.collection('highSchoolNews').add({
                'id': int(i["id"][0]),
                'date': i["date"],
                'folder': i["folder"],
                'title': i["title"],
                'link': i["link"],
                'timestamp': firestore.SERVER_TIMESTAMP
            })
    docDict = db.collection('count').document('highSchoolNews').get().to_dict()
    if len(highSchoolNewsSendData) != 0:
        howManyData = int(docDict['count']) + len(highSchoolNewsSendData)
        db.collection('count').document('highSchoolNews').update({'count': howManyData, 'update': firestore.SERVER_TIMESTAMP})

    returnData = {
        "getTime": getTime,
        "juniorCon": juniorConSendData,
        "juniorStudy": juniorStudySendData,
        "juniorSchoolNews": juniorSchoolNewsSendData,
        "highCon": highConSendData,
        "highStudy": highStudySendData,
        "highSchoolNews": highSchoolNewsSendData
    }
    print(returnData)
    return returnData


def getWaitSecs():
    max_wait = 7.0
    min_wait = 3.0
    mean_wait = 5.0
    sigma_wait = 1.0
    return min([max_wait, max([min_wait, round(random.normalvariate(mean_wait, sigma_wait))])])


if __name__ == "__main__":
    main()
