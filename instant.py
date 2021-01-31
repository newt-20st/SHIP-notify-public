from linebot.models import TextSendMessage
from linebot import LineBotApi
import datetime
from oauth2client.service_account import ServiceAccountCredentials
import json
import gspread
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time
import re
import random


def main():
    if os.environ['CHANNEL_TYPE'] == "public":
        YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
        YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]
    else:
        YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_DEV_CHANNEL_ACCESS_TOKEN"]
        YOUR_CHANNEL_SECRET = os.environ["YOUR_DEV_CHANNEL_SECRET"]

    line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)

    headers = {
        'Authorization': 'Bearer ' + YOUR_CHANNEL_ACCESS_TOKEN,
        'Content-type': 'application/json'
    }
    jsonOpen = open('other.json', 'r', encoding="utf-8_sig")
    jsonLoad = json.load(jsonOpen)
    broadcastEndPoint = "https://api.line.me/v2/bot/message/broadcast"
    jsonData = jsonLoad['instantWithFewMenu']
    jsonData['messages'][0]['text'] = "【2月からの機能追加・仕様変更について】\n・連絡事項の説明欄の文も取得するように\n・深夜と早朝は返事が遅くなることがある\n・通知の設定の種類が3種類に増えた\n https://newt-house.web.app/ship-notify/#release-note"
    print(jsonData)
    requests.post(broadcastEndPoint, json=jsonData, headers=headers)
    logMessage = "send message:" + \
        str(jsonData['messages'][0]['text'])+" send for all followed user."
    print(logMessage)


if __name__ == "__main__":
    main()