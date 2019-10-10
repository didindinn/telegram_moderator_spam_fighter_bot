#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters
import json
import time

DEBUG_GROUP = -1001198682178 # @bot_debug
SELF = 909398533
JOIN_TIME = {}
NEW_USER_WAIT_TIME = 3600 * 8

try:
	with open('ADMINS') as f:
		ADMINS = json.load(f)
except:
	ADMINS = {}

try:
	with open('BOT_OWNER') as f:
		BOT_OWNER = int(f.read())
except:
	BOT_OWNER = 0

try:
	with open('BLACKLIST') as f:
		BLACKLIST = f.readlines()
		BLACKLIST = [x.strip() for x in BLACKLIST]
		BLACKLIST = set([x for x in BLACKLIST if x])
except:
	BLACKLIST = set()

def saveAdmins():
	with open('ADMINS', 'w') as f:
		f.write(json.dumps(ADMINS, sort_keys=True, indent=2))

def saveBlacklist():
	with open('BLACKLIST', 'w') as f:
		f.write('\n'.join(sorted(BLACKLIST)))

def handleJoin(update, context):
	try:
		msg = update.message
		for member in msg.new_chat_members:
			if member.id == SELF:
				ADMINS[str(msg.chat.id)] = msg.from_user.id
				saveAdmins()
			elif not member.id in JOIN_TIME:
				JOIN_TIME[msg.chat.id] = JOIN_TIME.get(msg.chat.id, {})
				JOIN_TIME[msg.chat.id][member.id] = time.time()
	except Exception as e:
		print(e)
		tb.print_exc()

def isNewUser(msg):
	if not msg.chat.id in JOIN_TIME:
		return False
	if not msg.from_user.id in JOIN_TIME[msg.chat.id]:
		return False
	return JOIN_TIME[msg.chat.id][msg.from_user.id] > time.time() - NEW_USER_WAIT_TIME

def isMultiMedia(msg):
	return msg.photo or msg.sticker or msg.video

def containRiskyWord(msg):
	if not msg.text:
		return False
	for b in BLACKLIST:
		if b in url.lower():
			return True
	return False

def isBlockerUser(id):
	return str(id) in BLACKLIST

def shouldDelete(msg):
	return (isNewUser(msg) and (isMultiMedia(msg) or containRiskyWord(msg))) \
		or isBlockerUser(msg.from_user.id)

def getAuthor(msg):
	result = ''
	user = msg.from_user
	if user.first_name:
		result += ' ' + user.first_name
	if user.last_name:
		result += ' ' + user.last_name
	if user.username:
		result += '(@' + user.username + ')'
	return '[' + result + '](tg://user?id=' + str(user.id) + ')'

def deleteMsg(msg, bot):
	bot.send_message(chat_id=DEBUG_GROUP, text=getAuthor(msg) + ': ' + (msg.text or ''), parse_mode='Markdown')
	if msg.photo:
		# TODO: make this thread safe
		if msg.photo[0].get_file():
			msg.photo[0].get_file().download('tmp')
			bot.send_photo(chat_id=DEBUG_GROUP, photo=open('tmp', 'rb'))
			os.system('rm tmp')
	if msg.video:
		if msg.video.get_file():
			msg.video.get_file().download('tmp')
		bot.send_document(chat_id=DEBUG_GROUP, document=open('tmp', 'rb'))
	bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)

def markIfSpam(msg):
	# Currently only support bot owner
	if not msg.from_user.id == BOT_OWNER or msg.text != 'spam':
		return
	if msg.forward_from:
		BLACKLIST.add(str(msg.forward_from.id))
		saveBlacklist()
		bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)
		bot.delete_message(chat_id=msg.chat_id, message_id=msg.forward_from_message_id)

def handleGroup(update, context):
	try:
		msg = update.message
		if shouldDelete(msg):
			deleteMsg(msg, context.bot)
		markIfSpam(msg)
	except Exception as e:
		print(e)
		tb.print_exc()

def handlePrivate(update, context):
	try:
		return update.message.reply_text('Add me to the group you admin and promote me as Admin please.')
	except Exception as e:
		print(e)
		tb.print_exc()

with open('TOKEN') as f:
	TOKEN = f.readline().strip()

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, handleJoin))
dp.add_handler(MessageHandler(Filters.group, handleGroup))
dp.add_handler(MessageHandler(Filters.private, handlePrivate))

updater.start_polling()
updater.idle()