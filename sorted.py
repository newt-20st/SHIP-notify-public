import datetime
import json
import os
import random
import re

import discord
import requests
import wikipedia
from bs4 import BeautifulSoup
from discord.ext import tasks
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import search
import shipcheck
import shnews

load_dotenv()
TOKEN = os.environ['DISCORD_TOKEN']

intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    await client.wait_until_ready()
    wakeLogChannel = client.get_channel(817389202161270794)
    await wakeLogChannel.send('起動しました')
    game = discord.Game("prefix: [sh!]")
    await client.change_presence(activity=game)


@client.event
async def on_member_join(member):
    guild = member.guild
    unauthenticatedRole = guild.get_role(813015195881570334)
    await member.add_roles(unauthenticatedRole)


async def on_member_remove(member):
    await client.wait_until_ready()
    joinLeaveLogChannel = client.get_channel(810813680618831906)
    await joinLeaveLogChannel.send(member.name+"("+member.id+") が退出しました")


@client.event
async def on_message(message):
    await client.wait_until_ready()
    dmLogChannel = client.get_channel(817971315138756619)
    if message.author.bot:
        return
    if 'sh!' in message.content:
        if message.content == 'sh!':
            await message.channel.send('`sh!`はコマンドです。')
        elif message.content == 'sh!s' or message.content == 'sh!f' or message.content == 'sh!d':
            def check(msg):
                return msg.author == message.author
            try:
                await message.channel.send("ダウンロードリンクを表示したいもののidを入力してください")
                wait_message = await client.wait_for("message", check=check, timeout=60)
                data = search.main(wait_message.content)
                if len(data) == 0 or str(data[0][0]) == "{}":
                    embed = discord.Embed(
                        title=wait_message.content)
                    embed.add_field(name="error",
                                    value="指定されたidに該当するファイルがデータベースに見つかりませんでした", inline=False)
                else:
                    embed = discord.Embed(
                        title=wait_message.content, color=discord.Colour.from_rgb(50, 168, 82))
                    linkList = str(data[0][0])[1:-1].split(",")
                    body = ""
                    for link in linkList:
                        body += "`-` " + link + "\n"
                    embed.add_field(name="link", value=body, inline=False)
                await message.channel.send(embed=embed)
            except Exception as e:
                await message.channel.send("セッションがタイムアウトしました:"+str(e))
        elif 'search' in message.content or 'file' in message.content or 'download' in message.content:
            word = message.content.split()[1]
            data = search.main(word)
            if len(data) == 0 or str(data[0][0]) == "{}":
                embed = discord.Embed(title=word)
                embed.add_field(name="error",
                                value="指定されたidに該当するファイルがデータベースに見つかりませんでした", inline=False)
            else:
                embed = discord.Embed(
                    title=word, color=discord.Colour.from_rgb(50, 168, 82))
                linkList = str(data[0][0])[1:-1].split(",")
                body = ""
                for link in linkList:
                    body += "`-` " + link + "\n"
                embed.add_field(name="link", value=body, inline=False)
            await message.channel.send(embed=embed)
        # Wikipedia検索
        elif 'wiki' in message.content:
            word = message.content.split()[1]
            await message.channel.send('Wikipediaで`'+word+'`を検索...')
            wikipedia.set_lang("ja")
            response = wikipedia.search(word)
            if not response:
                await message.channel.send('Wikipediaで`'+word+'`に関連するページが見つかりませんでした')
            try:
                page = wikipedia.page(response[0])
                content = page.content.splitlines()[0]
                if len(content) > 1000:
                    content = content[0:1000] + "..."
                embed = discord.Embed(title=word)
                embed.add_field(name="wikipediaで検索した結果",
                                value=content.splitlines()[0], inline=False)
