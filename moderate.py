#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters

import requests
import json
from bs4 import BeautifulSoup
from html_telegraph_poster import TelegraphPoster

DEBUG_GROUP = -1001198682178 # @bot_debug

class Article(object):
	def __init__(self, title, author, text):
		self.title = title
		self.author = author
		self.text = text

try:
	with open('TELEGRAPH_TOKENS') as f:
		TELEGRAPH_TOKENS = json.load(f)
except:
	TELEGRAPH_TOKENS = {}

def saveTelegraphTokens():
	with open('TELEGRAPH_TOKENS', 'w') as f:
		f.write(json.dumps(TELEGRAPH_TOKENS, sort_keys=True, indent=2))

def getPoster(msg, id, forceMessageAuthUrl=False):
	if str(id) in TELEGRAPH_TOKENS:
		p = TelegraphPoster(access_token = TELEGRAPH_TOKENS[str(id)])
		if forceMessageAuthUrl:
			msgAuthUrl(msg, p)
		return p
	p = TelegraphPoster()
	r = p.create_api_token(msg.from_user.first_name, msg.from_user.username)
	TELEGRAPH_TOKENS[str(id)] = r['access_token']
	saveTelegraphTokens()
	msgAuthUrl(msg, p)
	return p

def msgAuthUrl(msg, p):
	r = p.get_account_info(fields=['auth_url'])
	msg.reply_text('Use this URL to login in 5 minutes: ' + r['auth_url'])

def wechat2Article(soup):
	title = soup.find("h2").text.strip()
	author = soup.find("a", {"id" : "js_name"}).text.strip()
	g = soup.find("div", {"id" : "js_content"})
	for img in g.find_all("img"):
		b = soup.new_tag("figure")
		b.append(soup.new_tag("img", src = img["data-src"]))
		img.append(b)
	for section in g.find_all("section"):
		b = soup.new_tag("p")
		b.append(BeautifulSoup(str(section), features="lxml"))
		section.replace_with(b)
	return Article(title, author, g)
	

def stackoverflow2Article(soup):
	title = soup.find("title").text.strip()
	title = title.replace('- Stack Overflow', '').strip()
	g = soup.find("div", class_ = "answercell")
	g = g.find("div", class_ = "post-text")
	for section in g.find_all("section"):
		b = soup.new_tag("p")
		b.append(BeautifulSoup(str(section), features="lxml"))
		section.replace_with(b)
	
	return Article(title, 'Stack Overflow', g)

def getAuthor(msg):
	result = ''
	user = msg.from_user
	if user.first_name:
		result += ' ' + user.first_name
	if user.last_name:
		result += ' ' + user.last_name
	if user.username:
		result += '(@' + user.username + ')'
	return result

def bbc2Article(soup):
	title = soup.find("h1").text.strip()
	g = soup.find("div", class_ = "story-body__inner")
	for elm in g.find_all('span', class_="off-screen"):
		elm.decompose()
	for elm in g.find_all('ul', class_="story-body__unordered-list"):
		elm.decompose()
	for elm in g.find_all('span', class_="story-image-copyright"):
		elm.decompose()
	for img in g.find_all("div", class_="js-delayed-image-load"):
		b = soup.new_tag("figure", width=img['data-width'], height=img['data-height'])
		b.append(soup.new_tag("img", src = img["data-src"], width=img['data-width'], height=img['data-height']))
		img.replace_with(b)
	for section in g.find_all("section"):
		b = soup.new_tag("p")
		b.append(BeautifulSoup(str(section), features="lxml"))
		section.replace_with(b)
	return Article(title, 'BBC', g)

NYT_ADS = '《纽约时报》推出每日中文简报'
def nyt2Article(soup):
	title = soup.find("meta", {"property": "twitter:title"})['content'].strip()
	author = soup.find("meta", {"name": "byl"})['content'].strip()
	g = soup.find("article")
	for link in g.find_all("a"):
		if not '英文版' in link.text:
			link.replace_with(link.text)
	for item in g.find_all("div", class_="article-header"):
		item.decompose()
	for item in g.find_all("div", class_="article-paragraph"):
		if item.text and NYT_ADS in item.text:
			item.decompose()
		elif item.text == '广告':
			item.decompose()
		else:
			wrapper = soup.new_tag("p")
			wrapper.append(BeautifulSoup(str(item), features="lxml"))
			item.replace_with(wrapper)
	for item in g.find_all("footer", class_="author-info"):
		for subitem in item.find_all("a"):
			if subitem.text and "英文版" in subitem.text:
				item.replace_with(subitem)
				break
	return Article(title, author + ' - NYT', g)

def telegraph2Article(soup):
	title = soup.find("meta", {"name": "twitter:title"})['content'].strip()
	author = soup.find("meta", {"property": "article:author"})['content'].strip()
	g = soup.find("article")
	item = g.find('h1')
	if item:
		item.decompose()
	item = g.find('address')
	if item:
		item.decompose()
	return Article(title, author, g)

def getArticle(URL):
	r = requests.get(URL)
	soup = BeautifulSoup(r.text, 'html.parser')
	if "mp.weixin.qq.com" in URL:
		return wechat2Article(soup)
	if "stackoverflow.com" in URL:
		return stackoverflow2Article(soup)
	if "bbc.com" in URL:
		return bbc2Article(soup)
	if "nytimes.com" in URL:
		return nyt2Article(soup)
	if "telegra.ph" in URL:
		return telegraph2Article(soup)
	return telegraph2Article(soup)

def getTelegraph(msg, URL):
	usr_id = msg.from_user.id
	p = getPoster(msg, usr_id)
	article = getArticle(URL)
	r = p.post(title = article.title, author = article.author, author_url = URL, text = str(article.text)[:80000])
	return r["url"]

def trimURL(URL):
	if not '://' in URL:
		return URL
	loc = URL.find('://')
	return URL[loc + 3:]

def exportImp(update, context):
	msg = update.message
	for item in msg.entities:
		if (item["type"] == "url"):
			URL = msg.text[item["offset"]:][:item["length"]]
			if not '://' in URL:
				URL = "https://" + URL
			u = trimURL(getTelegraph(msg, URL))
			msg.reply_text(u)
			r = context.bot.send_message(chat_id=DEBUG_GROUP, text=getAuthor(msg) + ': ' + u)

def export(update, context):
	try:
		exportImp(update, context)
	except Exception as e:
		print(e)
		tb.print_exc()

def command(update, context):
	try:
		if update.message.text and \
			('token' in update.message.text.lower() or 'auth' in update.message.text.lower()):
			id = update.message.from_user.id
			return getPoster(update.message, id, forceMessageAuthUrl=True)
		return update.message.reply_text('Feed me link, currently support wechat, bbc, stackoverflow, NYT')
	except Exception as e:
		print(e)
		tb.print_exc()

with open('TOKEN') as f:
	TOKEN = f.readline().strip()

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.text & Filters.private, export))
dp.add_handler(MessageHandler(Filters.private & Filters.command, command))

updater.start_polling()
updater.idle()