#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters
import json
import time
import os
import traceback as tb
from telegram_util import getDisplayUser, log_on_fail, getTmpFile

DEBUG_GROUP = -1001198682178  # @bot_debug
THIS_BOT = 909398533
JOIN_TIME = {}
NEW_USER_WAIT_TIME = 3600 * 8

try:
	with open('BOT_OWNER') as f:
		BOT_OWNER = int(f.read())
except:
	BOT_OWNER = 0

with open('BLACKLIST') as f:
	BLACKLIST = [x.strip() for x in f.readlines()]
	BLACKLIST = set([x for x in BLACKLIST if x])

def saveBlacklist():
	with open('BLACKLIST', 'w') as f:
		f.write('\n'.join(sorted(BLACKLIST)))

@log_on_fail()
def handleJoin(update, context):
	for member in update.message.new_chat_members:
		if member.id != THIS_BOT and member.id not in JOIN_TIME:
			JOIN_TIME[msg.chat.id] = JOIN_TIME.get(msg.chat.id, {})
			JOIN_TIME[msg.chat.id][member.id] = time.time()

def isNewUser(msg):
	if not msg.chat.id in JOIN_TIME:
		return False
	if not msg.from_user.id in JOIN_TIME[msg.chat.id]:
		return False
	return JOIN_TIME[msg.chat.id][
			msg.from_user.id] > time.time() - NEW_USER_WAIT_TIME

def isMultiMedia(msg):
	return msg.photo or msg.sticker or msg.video

def containRiskyWord(msg):
	if not msg.text:
		return False
	for b in BLACKLIST:
		if b.lower() in msg.text.lower():
			return True
	return False

def isBlockedUser(id):
	return str(id) in BLACKLIST

def shouldDelete(msg):
	return (isNewUser(msg) and (isMultiMedia(msg) or containRiskyWord(msg))) \
	 or isBlockedUser(msg.from_user.id)

def getGroupName(msg):
	return '[' + (msg.chat.title or str(msg.chat.id)) + 
		'](t.me/' + (msg.chat.username or '') + ')'

def getMsgType(msg):
	if msg.photo:
		return 'sent photo in'
	if msg.video:
		return 'sent video in'
	if msg.sticker:
		return 'sent sticker in'
	if msg.text:
		return 'texted'
	if msg.left_chat_member:
		return 'left'
	if msg.new_chat_members:
		return 'joined'
	return 'did some action'

@log_on_fail()
def deleteMsg(msg, bot):
	bot.send_message(
		chat_id=DEBUG_GROUP,
		text=getDisplayUser(msg.from_user) + ' ' + getMsgType(msg) + 
		' ' + getGroupName(msg) + ': ' + (msg.text or ''),
		parse_mode='Markdown',
		disable_web_page_preview=True)
	if msg.photo:
		filename = getTmpFile(msg)
		bot.send_photo(chat_id=DEBUG_GROUP, photo=open(filename, 'rb'))
		os.system('rm ' + filename)
	if msg.video:
		filename = getTmpFile(msg)
		bot.send_document(chat_id=DEBUG_GROUP, document=open(filename, 'rb'))
		os.system('rm ' + filename)
	msg.delete()


def ban(bad_user, bot):
	if bad_user.id == THIS_BOT:
		return  # don't ban the bot itself :p
	if str(bad_user.id) in BLACKLIST:
		bot.send_message(
				chat_id=DEBUG_GROUP,
				text=getDisplayUser(bad_user) + ' already banned',
				parse_mode='Markdown')
		return
	BLACKLIST.add(str(bad_user.id))
	saveBlacklist()
	bot.send_message(
			chat_id=DEBUG_GROUP,
			text=getDisplayUser(bad_user) + ' banned',
			parse_mode='Markdown')

def unban(not_so_bad_user, bot):
	if str(not_so_bad_user.id) not in BLACKLIST:
		bot.send_message(
				chat_id=DEBUG_GROUP,
				text=getDisplayUser(not_so_bad_user) + ' not banned',
				parse_mode='Markdown')
		return
	BLACKLIST.remove(str(not_so_bad_user.id))
	saveBlacklist()
	bot.send_message(
			chat_id=DEBUG_GROUP,
			text=getDisplayUser(not_so_bad_user) + ' unbanned',
			parse_mode='Markdown')

def markAction(msg, bot, action):
	if msg.reply_to_message and msg.reply_to_message.from_user.id == THIS_BOT:
		for item in msg.reply_to_message.entities:
			if item['type'] == 'text_mention':
				action(item.user, bot)
				return
		return
	if msg.reply_to_message:
		# in group, action and remove the command
		action(msg.reply_to_message.from_user, bot)
		bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)

def handleGroup(update, context):
	try:
		msg = update.message
		print(msg)
		if shouldDelete(msg):
			deleteMsg(msg, context.bot)
		if msg.from_user.id != BOT_OWNER:
			return
		# bot owner only
		if msg.text == 'spam' or msg.text == 'ban':
			markAction(msg, context.bot, ban)
		if msg.text == 'spam':
			context.bot.delete_message(
				chat_id=msg.chat_id, message_id=msg.reply_to_message.message_id)
		if msg.text == 'unban':
			# not tested
			markAction(msg, context.bot, unban)
	except Exception as e:
		print(e)
		tb.print_exc()

def handlePrivate(update, context):
	update.message.reply_text(
		'Add me to the group you admin and promote me as Admin please.')

def deleteMsgHandle(update, context):
	deleteMsg(update.message, context.bot)

with open('TOKEN') as f:
	TOKEN = f.readline().strip()

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(
		MessageHandler(Filters.status_update.new_chat_members, handleJoin))
dp.add_handler(
		MessageHandler(Filters.status_update.new_chat_members, deleteMsgHandle), group = 1)
dp.add_handler(
		MessageHandler(Filters.status_update.left_chat_member, deleteMsgHandle), group = 1)
dp.add_handler(MessageHandler(Filters.group, handleGroup), group = 2)
dp.add_handler(MessageHandler(Filters.private, handlePrivate), group = 3)

updater.start_polling()
updater.idle()
