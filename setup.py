import os
import sys

def setup(mode):
	RUN_COMMAND = 'nohup python3 moderate.py &'

	with open('TOKEN') as f:
		TOKEN = f.readline().strip()

	if mode != 'reload':
		os.system('curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py')
		os.system('python3 get-pip.py')
		os.system('rm get-pip.py')

		os.system('pip3 install -r requirements.txt')
		os.system('pip3 install python-telegram-bot --upgrade') # need to use some experiement feature, e.g. message filtering

	return os.system(RUN_COMMAND)


if __name__ == '__main__':
	if len(sys.argv) > 1:
		setup(sys.argv[1])
	else:
		setup('')