import argparse
import requests
import base64
import time
import os
from os import listdir
from os.path import isfile, join
import csv
import datetime
import logging
import sys
import calendar


version = 'v0.0.1'

def main():

	print('[{0}] [INFO] Starting Dalla-Data {1}'.format(getTime(), version))

	parser = argparse.ArgumentParser()

	parser.add_argument("-u", "--username", default='', help="the router admin username")
	parser.add_argument("-p", "--password", default='', help="the router admin password")
	parser.add_argument("-i", "--interval", type=int, default=60, help="the interval in seconds to update the log files")
	parser.add_argument("-d", "--device-directory", default='', help="directory to save device logs")
	#parser.add_argument("-l", "--service-log-file", default='', help="directory to save device logs")
	parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + version)

	args = parser.parse_args()

	deviceDir = args.device_directory

	if deviceDir == '':
		print('Please provide a directory for the data logs with -d')
		exit()

	interval = args.interval

	if (deviceDir == ''):
		deviceDir = 'devices'

	if (args.username == '' or args.password == ''):
		print('[ERROR] Please supply username and password')
		exit()

	if (interval == 0):
		print('[ERROR] Interval needs to be > 0')
		exit()

	sessionHeaders = initSession(args.username, args.password)

	abort = False
	while (True):
		try:
			timeKey = int(time.time()) # UTC TIME!

			devices = {}

			print('[{0}] [INFO] Fetching device stats...'.format(getTime()))
			devices = getDeviceRecords(sessionHeaders, timeKey)

			if (len(devices) != 0):
				print('[{0}] [INFO] Logging device stats to log'.format(getTime()))
				logDeviceStats(devices, deviceDir)
			else:
				print('[{0}] [ERROR] Failed to get device records from router.'.format(getTime()))
				# Getting records fail, try to logout
				# REVIEW: Does this work when timout occurs
				logout(sessionHeaders)

			if (abort == False):
				time.sleep(interval)
			else:
				break

		except (KeyboardInterrupt, SystemExit) as e:
			print(e)
			print('\n[{0}] [INFO] Exiting. Please wait...'.format(getTime()))
			time.sleep(1)
			abort = True

def getTime():
	timeKey = int(time.time()) # UTC TIME!
	localTimeFormated = time.strftime('%Y-%M-%d %H:%M:%S', time.localtime(timeKey))
	return localTimeFormated

def validateDevices(statsDictArray, timeKey):
	"""Strip invalid entries and parse valid entries
	"""

	newDictArray = []

	for statsDict in statsDictArray:
		# Skip invalid intries
		if (len(statsDict) == 12):
			# Strip extra data,
			# Convert Dec IP to readable IP
			tmpDict = { 'MAC Address': statsDict['macAddress'],
						'IP Address': decStrToIpStr(statsDict['ipAddress']),
						'Total Bytes': int(statsDict['totalBytes']),
						'Time': timeKey}

			newDictArray.append(tmpDict)

	return newDictArray


def getDeviceRecords(session, timeKey):
	""" Poll the router for the current device statistics

	These records need to be compared to a previous set to calculate the
	Delta
	"""

	# Configure page specific headers
	url = 'http://192.168.1.1/cgi?1&5'
	session.headers.update({'Referer': 'http://192.168.1.1/mainFrame.htm'})
	data ='[STAT_CFG#0,0,0,0,0,0#0,0,0,0,0,0]0,0\r\n[STAT_ENTRY#0,0,0,0,0,0#0,0,0,0,0,0]1,0\r\n'

	try:
		r = session.post(url=url, data=data, timeout=1)
	except requests.ConnectionError:
		print('[ERROR] Network unreachable!')
		return {}
	except requests.ReadTimeout:
		print('[ERROR] Connection timeout!')
		return {}
	except KeyboardInterrupt:
		#print('[ERROR] KeyboardInterrupt during getDeviceRecords()')
		raise
	except:
		print('[ERROR] Unexpected error: ', sys.exc_info()[0])
		return {}

	rawStats = r.text

	error = rawStats.split('\n')

	if (error[-1] != '[error]0'):
		print('[{0}] [ERROR] Failed to get device records from router!'.format(getTime()))
		if (r.text == '<html><head><title>500 Internal Server Error</title></head><body><center><h1>500 Internal Server Error</h1></center></body></html>'):
			print('[{0}] Another admin has logged in!'.format(getTime()))
		else:
			print('\t' + r.text)

		return []

	dictArray = []
	tmpDict = {}

	arr = rawStats.split("\n")

	for i in range(0, len(arr)):
		"""
		Loop through every line
		If the line is a title
			begin split and read into dict

		if we encounter another title
			insert old dict into array and start new dict and increase index

		"""

		arr[i] = arr[i].strip()

		# start of a new header
		if (arr[i][0] == '['):

			dictArray.append(tmpDict)
			tmpDict = {}
			next # skip the header

		tmp = arr[i].split('=')

		# Add key=value
		if (len(tmp) == 2):
			tmpDict[tmp[0]] = tmp[1]

	# Manipulate dict array to get what we need
	init = validateDevices(dictArray, timeKey)

	logout(session)

	return init

def logDeviceStats(statsDictArray, deviceDir):
	"""Save device dict array to log files
	"""
	"""
	filename: M-A-C_I.P
	Time, Total Bytes
	"""

	if (not os.path.exists(deviceDir)):
		os.makedirs(deviceDir)

	for statsDict in statsDictArray:

		# Generate file name
		mac = statsDict['MAC Address'].replace(':', '-')
		ip = statsDict['IP Address']
		fileName = str(deviceDir + '/' + mac + '_' + ip + '.csv')

		# csv fields
		timeKey = statsDict['Time']
		totalBytes = statsDict['Total Bytes']

		# new device, set up csv for it
		header = False
		if (os.path.isfile(fileName) == False):
			header = True

		output = open(fileName, 'a')

		if (header):
			output.write('Time, Total Bytes\n')

		output.write('{0}, {1}\n'.format(timeKey, totalBytes))
		output.close()


def getIpFromFileName(name):
	result = name.split('_')
	result = str(result[1])[:-4]

	return result

def getMacFromFileName(name):
	result = name.split('_')
	result = result[0].replace('-', ':')

	return result

def initSession(username, password):
	session = requests.session()

	raw = username + ':' + password
	encoded = base64.b64encode(raw.encode('utf-8'))

	auth = 'Basic ' + encoded.decode('utf-8')
	cookie = 'Authorization=' + auth

	session.headers = {
		'Host': '192.168.1.1',
		'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:46.0) Gecko/20100101 Firefox/46.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Content-Type': 'text/plain',
		'Cookie': cookie,
		'Referer': 'http://192.168.1.1/',
		'Connection': 'keep-alive'
	}

	return session

def decStrToIpStr(dec):
	binStr = bin(int(dec))

	binStr = binStr[2:]
	finalStr = ''

	"""
	0: 0, 8 (8*0), ()
	1: 8, 16 (8*1)
	2: 16, 24 (8*2)
	3: 24, 32 (8*3)
	"""

	for i in range(0, 4):
		tmp = binStr[8 * i : 8 * (i + 1)]
		tmp = int(tmp, 2)
		finalStr += str(tmp) + '.'

	return finalStr[:-1]


def logout(session):
	# Configure page specific headers
	url = 'http://192.168.1.1/cgi?8'
	session.headers.update({'Referer': 'http://192.168.1.1/MenuRpm.htm'})
	data ='[/cgi/logout#0,0,0,0,0,0#0,0,0,0,0,0]0,0\r\n'

	try:
		r = session.post(url=url, data=data)
	except KeyboardInterrupt:
		#print('[ERROR] KeyboardInterrupt during getDeviceRecords()')
		raise
	except:
		print('[{0}] [ERROR] Unexpected error: {1}'.format(getTime(), sys.exc_info()[0]))
		return


	if (r.text != '[cgi]0\n[error]0'):
		print('[{0}] [ERROR] Logout failed:'.format(getTime()))

		if (r.text == '<html><head><title>500 Internal Server Error</title></head><body><center><h1>500 Internal Server Error</h1></center></body></html>'):
			print('[{0}] Another admin has logged in!'.format(getTime()))
		else:
			print('\t' + r.text)


main()
