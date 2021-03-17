import pyrebase
import os
import psycopg2
from psycopg2.extras import DictCursor
import json
import time
import datetime
import requests
import re
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.environ['DATABASE_URL']

now = datetime.datetime.now()
getTime = now.strftime('%Y-%m-%d %H:%M:%S')

config = {
    'apiKey': os.environ['FIREBASE_API_KEY'],
    'authDomain': os.environ['FIREBASE_AUTH_DOMAIN'],
    "databaseURL": "xxxxxx",
    'storageBucket': os.environ['FIREBASE_STORAGE_BUCKET']
}
firebase = pyrebase.initialize_app(config)


def main():
    if os.environ['STATUS'] == "local":
        CHROME_DRIVER_PATH = 'C:\chromedriver.exe'
        DOWNLOAD_DIR = 'D:\Downloads'
    else:
        CHROME_DRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
        DOWNLOAD_DIR = '/app/tmp'
        os.mkdir(DOWNLOAD_DIR)
    options = webdriver.ChromeOptions()
    options.add_argument('start-maximized')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    prefs = {'download.default_directory': DOWNLOAD_DIR,
             'download.prompt_for_download': False}
    options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH,
                              options=options)
    driver.command_executor._commands['send_command'] = ('POST',
                                                         '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior',
              'params': {'behavior': 'allow',
                         'downloadPath': DOWNLOAD_DIR}}
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
        driver.get("https://ship.sakae-higashi.jp/menu.php")
        menu = driver.page_source
        menuSoup = BeautifulSoup(menu, 'html.parser')
        menuStatus = menuSoup.find_all('table')[1].text
        menuBtn = menuSoup.find_all('table')[2].find_all('input')[1]
        if count == 0 and '中学校' in menuStatus:
            driver.find_element_by_name('cheng_hi').click()
        elif count == 1 and '高等学校' in menuStatus:
            driver.find_element_by_name('cheng_jr').click()
        driver.get(
            "https://ship.sakae-higashi.jp/connection/search.php?obj_id=&depth=&search=&s_y=2011&s_m=01&s_d=01&e_y=2030&e_m=12&e_d=31")
        con = driver.page_source
        conSoup = BeautifulSoup(con, 'html.parser')
        conLinks = conSoup.find_all(class_='allc')[0].find_all('a')
        conEachPage = []
        for conLink in conLinks:
            conOnclick = conLink.get('onclick')
            conId = re.findall("'([^']*)'", conOnclick)[0]
            time.sleep(2)
            driver.get(
                "https://ship.sakae-higashi.jp/sub_window_anke/?obj_id="+conId+"&t=3")
            conEachPage.append(driver.page_source)
        conBody = conSoup.find("body")
        conTrs = conSoup.find_all(class_='allc')[0].find_all('tr')
        conTrs.pop(0)
        conList = []
        conc = 0
        for conTr in conTrs:
            time.sleep(2)
            eachconList = []
            conTrTds = conTr.find_all('td')
            try:
                stage = conTrTds[2].find('a').get('onclick')
                eachconList.append(re.findall("'([^']*)'", stage))
            except:
                eachconList.append([0, 0])
            eachconList.append(conTrTds[0].text)
            try:
                eachconList.append(conTrTds[1].find('span').get('title'))
            except:
                eachconList.append(conTrTds[1].text)
            eachconList.append(conTrTds[2].text.replace("\n", ""))
            conEachPageSoup = BeautifulSoup(conEachPage[conc], 'html.parser')
            conPageMain = conEachPageSoup.find_all(
                class_='ac')[0].find_all("table")[1]
            conPageDescription = conPageMain.find_all(
                "table")[-2].text.replace("\n", "")
            eachconList.append(conPageDescription)
            conPageLinks = conPageMain.find_all(
                "table")[-1].find_all("a")
            conPageLinkList = []
            for eachConPageLink in conPageLinks:
                driver.get("https://ship.sakae-higashi.jp" +
                           eachConPageLink.get("href"))
                result = re.match(".*name=(.*)&size.*",
                                  eachConPageLink.get("href"))
                print(result.group(1))
                time.sleep(3)
                if os.environ['STATUS'] == "local":
                    filepath = 'D:\Downloads/' + result.group(1)
                else:
                    filepath = DOWNLOAD_DIR + '/' + result.group(1)
                storage = firebase.storage()
                if count == 0:
                    schooltype = "high"
                elif count == 1:
                    schooltype = "junior"
                try:
                    storage.child(
                        'pdf/'+schooltype+'-con/'+str(eachconList[0][0])+'/'+result.group(1)).put(filepath)
                    conPageLinkList.append(storage.child(
                        'pdf/'+schooltype+'-con/'+str(eachconList[0][0])+'/'+result.group(1)).get_url(token=None))
                except Exception as e:
                    print(str(e))
            eachconList.append(conPageLinkList)
            conList.append(eachconList)
            conc += 1
        print(conList)

        driver.get(
            "https://ship.sakae-higashi.jp/study/search.php?obj_id=&depth=&search=&s_y=2011&s_m=01&s_d=01&e_y=2030&e_m=12&e_d=31")
        study = driver.page_source
        studySoup = BeautifulSoup(study, 'html.parser')
        studyLinks = studySoup.find_all(class_='allc')[0].find_all('a')
        studyEachPage = []
        for studyLink in studyLinks:
            studyOnclick = studyLink.get('onclick')
            studyId = re.findall("'([^']*)'", studyOnclick)[0]
            time.sleep(2)
            driver.get(
                "https://ship.sakae-higashi.jp/sub_window_anke/?obj_id="+studyId+"&t=7")
            studyEachPage.append(driver.page_source)
        studyBody = studySoup.find("body")
        studyTrs = studySoup.find_all(class_='allc')[0].find_all('tr')
        studyTrs.pop(0)
        studyList = []
        studyc = 0
        for studyTr in studyTrs:
            eachstudyList = []
            studyTrTds = studyTr.find_all('td')
            try:
                stage = studyTrTds[2].find('a').get('onclick')
                eachstudyList.append(re.findall("'([^']*)'", stage))
            except:
                eachstudyList.append([0, 0])
            eachstudyList.append(studyTrTds[0].text)
            try:
                eachstudyList.append(studyTrTds[1].find('span').get('title'))
            except:
                eachstudyList.append(studyTrTds[1].text)
            eachstudyList.append(studyTrTds[2].text.replace("\n", ""))
            studyEachPageSoup = BeautifulSoup(
                studyEachPage[studyc], 'html.parser')
            try:
                studyPageMain = studyEachPageSoup.find_all(
                    class_='ac')[0].find_all("table")[1]
                studyPageLinks = studyPageMain.find_all(
                    "table")[-1].find_all("a")
            except Exception as e:
                print(str(e))
            studyPageLinkList = []
            for eachstudyPageLink in studyPageLinks:
                driver.get("https://ship.sakae-higashi.jp" +
                           eachstudyPageLink.get("href"))
                result = re.match(".*name=(.*)&size.*",
                                  eachstudyPageLink.get("href"))
                print(result.group(1))
                time.sleep(3)
                if os.environ['STATUS'] == "local":
                    filepath = 'D:\Downloads/' + result.group(1)
                else:
                    filepath = DOWNLOAD_DIR + '/' + result.group(1)
                storage = firebase.storage()
                if count == 0:
                    schooltype = "high"
                elif count == 1:
                    schooltype = "junior"
                try:
                    storage.child(
                        'pdf/'+schooltype+'-study/'+str(eachstudyList[0][0])+'/'+result.group(1)).put(filepath)
                    studyPageLinkList.append(storage.child(
                        'pdf/'+schooltype+'-study/'+str(eachstudyList[0][0])+'/'+result.group(1)).get_url(token=None))
                except Exception as e:
                    print(str(e))
            eachstudyList.append(studyPageLinkList)
            studyList.append(eachstudyList)
            studyc += 1
        print(studyList)

        driver.get("https://ship.sakae-higashi.jp/menu.php")
        menu = driver.page_source
        menuSoup = BeautifulSoup(menu, 'html.parser')
        menuStatus = menuSoup.find_all('table')[1].text
        if '中学校' in menuStatus:
            juniorConList = conList
            juniorStudyList = studyList
        elif '高等学校' in menuStatus:
            highConList = conList
            highStudyList = studyList
        count += 1
    driver.quit()

    with get_connection() as conn:
        with conn.cursor() as cur:
            juniorConSendData = []
            juniorStudySendData = []
            for i in juniorConList:
                if i[0][0] != 0:
                    cur.execute('SELECT EXISTS (SELECT * FROM con_junior WHERE id = %s)',
                                [int(i[0][0])])
                    (b,) = cur.fetchone()
                    if b == False:
                        date = i[1].replace(
                            "年", "/").replace("月", "/").replace("日", "")
                        cur.execute('INSERT INTO con_junior (id, date, folder, title, description, link) VALUES (%s, %s, %s, %s, %s, %s)', [
                                    i[0][0], date, i[2], i[3], i[4], i[5]])
                        juniorConSendData.append(
                            [i[0][0], date, i[2], i[3], i[4], i[5]])
            for i in juniorStudyList:
                if i[0][0] != 0:
                    cur.execute('SELECT EXISTS (SELECT * FROM study_junior WHERE id = %s)',
                                [int(i[0][0])])
                    (b,) = cur.fetchone()
                    if b == False:
                        date = i[1].replace(
                            "年", "/").replace("月", "/").replace("日", "")
                        cur.execute('INSERT INTO study_junior (id, date, folder, title, link) VALUES (%s, %s, %s, %s, %s)', [
                                    i[0][0], date, i[2], i[3], i[4]])
                        juniorStudySendData.append(
                            [i[0][0], date, i[2], i[3], i[4]])
            highConSendData = []
            for i in highConList:
                if i[0][0] != 0:
                    cur.execute('SELECT EXISTS (SELECT * FROM con_high WHERE id = %s)',
                                [int(i[0][0])])
                    (b,) = cur.fetchone()
                    if b == False:
                        date = i[1].replace(
                            "年", "/").replace("月", "/").replace("日", "")
                        cur.execute('INSERT INTO con_high (id, date, folder, title, description, link) VALUES (%s, %s, %s, %s, %s, %s)', [
                                    i[0][0], date, i[2], i[3], i[4], i[5]])
                        highConSendData.append(
                            [i[0][0], date, i[2], i[3], i[4], i[5]])
            highStudySendData = []
            for i in highStudyList:
                if i[0][0] != 0:
                    cur.execute('SELECT EXISTS (SELECT * FROM study_high WHERE id = %s)',
                                [int(i[0][0])])
                    (b,) = cur.fetchone()
                    if b == False:
                        date = i[1].replace(
                            "年", "/").replace("月", "/").replace("日", "")
                        cur.execute('INSERT INTO study_high (id, date, folder, title) VALUES (%s, %s, %s, %s, %s)', [
                                    i[0][0], date, i[2], i[3], i[4]])
                        highStudySendData.append(
                            [i[0][0], date, i[2], i[3], i[4]])
        conn.commit()
    sortedJuniorConSendData = []
    for value in reversed(juniorConSendData):
        sortedJuniorConSendData.append(value)
    sortedJuniorStudySendData = []
    for value in reversed(juniorStudySendData):
        sortedJuniorStudySendData.append(value)
    sortedHighConSendData = []
    for value in reversed(highConSendData):
        sortedHighConSendData.append(value)
    sortedHighStudySendData = []
    for value in reversed(highStudySendData):
        sortedHighStudySendData.append(value)
    print(sortedJuniorConSendData)
    print(sortedJuniorStudySendData)
    print(sortedHighConSendData)
    print(sortedHighStudySendData)
    nowHour = int(datetime.datetime.now().strftime("%H"))
    nowMinute = int(datetime.datetime.now().strftime("%M"))
    return sortedJuniorConSendData, sortedJuniorStudySendData, sortedHighConSendData, sortedHighStudySendData, getTime


def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def getWaitSecs():
    # 画面の待機秒数の取得
    max_wait = 7.0  # 最大待機秒
    min_wait = 3.0  # 最小待機秒
    mean_wait = 5.0  # 平均待機秒
    sigma_wait = 1.0  # 標準偏差（ブレ幅）
    return min([max_wait, max([min_wait, round(random.normalvariate(mean_wait, sigma_wait))])])


if __name__ == "__main__":
    main()
