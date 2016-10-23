import requests
import base64
import StringIO
import time
import os
import numpy as np
from os import listdir
from os.path import isfile, join

"""
Get device stats -> csv
    CSV:
        Time, Total Byes, Deleta Bytes, On-Peak, Off-Peak

Take each user,
    For each MAC in user
    User += Mac stats
    -> csv

Take each user
commune += user
    -> csv

"""

"""
Get Raw Statistics
Parse Device Statistics
    - Open each csv, get last entry, calculate delta, peak, and off-peak, append
Load User map
Parse user Statistics
    - Open each csv, get last entry, calculate delta, peak, and off-peak, append
Parse commune statistics
    - Open csv, get last entry, calculate delta, peak, and off-peak, append

"""

def main():
    interval = 1
    username = 'admin'
    password = 'admin'
    deviceLogPath = 'devices/'
    userLogPath = 'users/'
    communeLogFile = 'commune.csv'
    userMapPath = 'user-map.csv'

    oldDeviceStats = []
    userStats = []

    userMap = loadUserMap(userMapPath)
    oldDeviceStats = loadDeviceStats(deviceLogPath)

    while (True):
        timeKey = int(time.time())

        session = requests.session()
        initSession(username, password, session)

        deviceStats = getDeviceStats(session)
        deviceStats = updateDeviceStats(oldDeviceStats, deviceStats, deviceLogPath, timeKey)

        #print deviceStats

        #print oldDeviceStats

        userStats = getUserStatsRAM(deviceStats, userMap, timeKey)
        #userStats = getUserStats(deviceLogPath, userLogPath, userMapPath, timeKey)
        logUserStats(userLogPath, userStats)

        communeStats = getCommuneStats(userStats, communeLogFile, timeKey)
        logCommuneStats(communeLogFile, communeStats)

        oldDeviceStats = deviceStats

        time.sleep(interval)

def generateStats(username, password, deviceLogPath, userLogPath, communeLogFile, userMapPath):
    timeKey = int(time.time())

    session = requests.session()
    initSession(username, password, session)

    deviceStats = getDeviceStats(session)

    logDeviceStats(deviceLogPath, deviceStats, timeKey)

    userStats = getUserStatsRAM(deviceLogPath, userLogPath, userMapPath, timeKey)
    logUserStats(userLogPath, userStats)

    communeStats = getCommuneStats(userLogPath, communeLogFile, timeKey)
    logCommuneStats(communeLogFile, communeStats)

    print communeStats

def loadDeviceStats(deviceLogPath):
    """
    Go through the device logs, and add up the last row
    """

    deviceStatsArray = []

    try:
        os.mkdir(deviceLogPath)
    except OSError:
        i = 5

    onlyfiles = [f for f in listdir(deviceLogPath) if isfile(join(deviceLogPath, f))]

    for devicecsv in onlyfiles:
        # get log file info

        mac = getMacFromFileName(devicecsv)
        ip = getIpFromFileName(devicecsv)

        #print('MAC = ' + mac)

        # load csv
        csv = np.genfromtxt(deviceLogPath + devicecsv, delimiter=',', dtype=long)

        tmpDevice = {}
        tmpDevice['Time'] = csv[-1][0]
        tmpDevice['macAddress'] = mac
        tmpDevice['ipAddress'] = ip
        tmpDevice['totalBytes'] = csv[-1][1]
        tmpDevice['Delta Bytes'] = csv[-1][2]
        tmpDevice['On-Peak'] = csv[-1][3]
        tmpDevice['Off-Peak'] = csv[-1][4]
        deviceStatsArray.append(tmpDevice)

    return deviceStatsArray

def getUserStatsRAM(deviceStats, userMap, timeKey):
    """
    Go through the device logs, and add up the last row
    """
    userStatsArray = []

    unknownUser = {}
    unknownUser['Name'] = 'Unknown'
    unknownUser['Time'] = timeKey
    unknownUser['Total Bytes'] = 0
    unknownUser['Delta Bytes'] = 0
    unknownUser['On-Peak'] = 0
    unknownUser['Off-Peak'] = 0

    userStatsArray.append(unknownUser)

    # Open device lig files that belong to each user

    for deviceDict in deviceStats:
        # get log file info

        mac = deviceDict['macAddress']
        ip = deviceDict['ipAddress']

        #print('MAC = ' + mac

        if (deviceDict['Time'] != timeKey):
            print('Time key mismatch!')

        # does this MAC belong to a user?
        # yes, add the device values to the user dict
        if (userMap.has_key(mac)):
            # print(mac + ' belongs to ' + userMap[mac])

            # See if this user exists in the userStatsArray, if so, append, else create new user
            found = False
            for user in userStatsArray:
                if (user['Name'] == userMap[mac]):
                    found = True
                    user['Total Bytes'] += deviceDict['totalBytes']
                    user['Delta Bytes'] += deviceDict['Delta Bytes']
                    user['On-Peak'] += deviceDict['On-Peak']
                    user['Off-Peak'] += deviceDict['Off-Peak']

            if (found == False):
                tmpUser = {}
                tmpUser['Name'] = userMap[mac]
                tmpUser['Time'] = timeKey
                tmpUser['Total Bytes'] = deviceDict['totalBytes']
                tmpUser['Delta Bytes'] = deviceDict['Delta Bytes']
                tmpUser['On-Peak'] = deviceDict['On-Peak']
                tmpUser['Off-Peak'] = deviceDict['Off-Peak']
                userStatsArray.append(tmpUser)
        else:
            # print(mac + ' not found in userMap!')
            # Mac does not belong to user, add to the unknown user at index 0
            userStatsArray[0]['Total Bytes'] += deviceDict['totalBytes']
            userStatsArray[0]['Delta Bytes'] += deviceDict['Delta Bytes']
            userStatsArray[0]['On-Peak'] += deviceDict['On-Peak']
            userStatsArray[0]['Off-Peak'] += deviceDict['Off-Peak']

    return userStatsArray

def updateDeviceStats(prevStats, newStats, deviceLogPath, timeKey):
    #print 'Updating device stats...'

    """
    Calculate delta, peak, and off-peak, then also writes to the log files?
    """

    """
    FORMAT:

    filename: M-A-C_I.P

    Time, Total Bytes, Delta Bytes, On-Peak, Off-Peak

    """

    try:
        os.mkdir(deviceLogPath)
    except OSError:
        i = 5

    for newDeviceDict in newStats:
        # file name
        newDeviceDict['Time'] = timeKey

        mac = newDeviceDict['macAddress'].replace(':', '-')
        ip = newDeviceDict['ipAddress']
        fileName = str(deviceLogPath + mac + '_' + ip + '.csv')

        # csv fields
        totalBytes = newDeviceDict['totalBytes']

        # new device, set up csv for it
        if (os.path.isfile(fileName) == False):
            print 'New device: ' + mac + '_' + ip

            # TODO: P and O times
            # add new keys
            newDeviceDict['Delta Bytes'] = 0
            newDeviceDict['On-Peak'] = totalBytes
            newDeviceDict['Off-Peak'] = 0

            output = open(fileName, 'a')
            output.write('Time, Total Bytes, Delta Bytes, On-Peak, Off-Peak\n')

            output.write('{0}, {1}, {2}, {3}, {4}\n'.format(timeKey, totalBytes, newDeviceDict['Delta Bytes'], newDeviceDict['On-Peak'], newDeviceDict['Off-Peak']))
            output.close()
        else:
            # search for matching device dict in prev dict
            found = False

            for oldDeviceDict in prevStats:
                # look for match
                if (oldDeviceDict['macAddress'] == newDeviceDict['macAddress']):
                    if (oldDeviceDict['ipAddress'] == newDeviceDict['ipAddress']):
                        #print mac + "_" + ip + ':'

                        found = True
                        newDeviceDict['Delta Bytes'] = totalBytes - oldDeviceDict['totalBytes']

                        #print('Delta = {0} - {1} = {2}'.format(totalBytes, oldDeviceDict['totalBytes'], newDeviceDict['Delta']))

                        if (newDeviceDict['Delta Bytes'] < 0):
                            newDeviceDict['Delta Bytes'] = totalBytes
                            print 'Negative delta!'

                        # TODO: if time, peak | O
                        if (oldDeviceDict.has_key("On-Peak")):

                            newDeviceDict['On-Peak'] = newDeviceDict['Delta Bytes'] + oldDeviceDict['On-Peak']
                            #print('On-Peak = {0} + {1} = {2}'.format(totalBytes, newDeviceDict['Delta'], newDeviceDict['On-Peak']))
                        else:
                            # Missing data, resort to csv
                            #print ('old Dict has not yet been converted, loading from csv')
                            csv = np.genfromtxt(fileName, delimiter=",", dtype=long)
                            newDeviceDict['On-Peak'] = newDeviceDict['Delta Bytes'] + csv[-1][3]
                            #print('On-Peak = {0} + {1} = {2}'.format(newDeviceDict['Delta'], csv[-1][3], newDeviceDict['On-Peak']))

                        newDeviceDict['Off-Peak'] = 0

                        output = open(fileName, 'a')
                        output.write('{0}, {1}, {2}, {3}, {4}\n'.format(timeKey, totalBytes, newDeviceDict['Delta Bytes'], newDeviceDict['On-Peak'], newDeviceDict['Off-Peak']))
                        output.close()

            if (found == False):
                print('Device dict mismatch!')

    updatedDeviceStats = newStats
    return updatedDeviceStats



def getDeviceStats(session):

    url = 'http://192.168.1.1/cgi?1&5'

    session.headers.update({'Referer': 'http://192.168.1.1/mainFrame.htm'})
    data ='[STAT_CFG#0,0,0,0,0,0#0,0,0,0,0,0]0,0\r\n[STAT_ENTRY#0,0,0,0,0,0#0,0,0,0,0,0]1,0\r\n'

    r = session.post(url=url, data=data)

    rawStats = r.text
    """
    macAddress
    ipAddress
    totalBytes
    """

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

        #print arr[i]

        if (arr[i][0] == '['):
            #print 'Adding tmpDict to dictArray'
            dictArray.append(tmpDict)
            tmpDict = {}

            #print 'Start Collecting...'
            next

        tmp = arr[i].split('=')

        if (len(tmp) == 2):
            #print 'Adding ' + tmp[0] + '=' + tmp[1] + ' to tmpDict'
            tmpDict[tmp[0]] = tmp[1]

    cleaned = cleanStatsDictArray(dictArray)
    fixed = fixIpsInDictArray(cleaned)
    squash = squashStatsDictArray(cleaned)
    #dumpDictArrayToCsv('stats/', squash)

    return squash

def logDeviceStats(prefix, statsDictArray, timeKey):
    """
    FORMAT:

    filename: M-A-C_I.P

    Time, Total Bytes, Delta Bytes, On-Peak, Off-Peak

    """

    try:
        os.mkdir(prefix)
    except OSError:
        i = 5

    for statsDict in statsDictArray:
        # file name
        mac = statsDict['macAddress'].replace(':', '-')
        ip = statsDict['ipAddress']
        fileName = str(prefix + mac + '_' + ip + '.csv')

        # csv fields
        totalBytes = statsDict['totalBytes']

        # new device, set up csv for it
        if (os.path.isfile(fileName) == False):
            output = open(fileName, 'a')
            output.write('Time, Total Bytes, Delta Bytes, On-Peak, Off-Peak\n')
            # TODO: P and O times
            output.write('{0}, {1}, {2}, {3}, {4}\n'.format(timeKey, totalBytes, 0, totalBytes, 0))
        else:
            #print(fileName)
            # we saw this device before, parse the csv and get the last values.
            # calculate delta, P and O
            csv = np.genfromtxt(fileName, delimiter=",", dtype=long)
            #print(csv[-1][1])
            #-1 = last row,
            delta = totalBytes - csv[-1:][0][1]

            if (delta < 0):
                delta = totalBytes

            # TODO: if time, peak | O
            peak = csv[-1][3] + delta
            output = open(fileName, 'a')
            output.write('{0}, {1}, {2}, {3}, {4}\n'.format(timeKey, totalBytes, delta, peak, 0))
            output.close()

def logUserStats(userLogPath, userStatsArray):
    """
    Append the user data to their csv files
    """

    try:
        os.mkdir(userLogPath)
    except OSError:
        i = 5

    #print userStatsArray

    for user in userStatsArray:
        fileName = userLogPath + user['Name'] + '.csv'
        header = False

        if (os.path.isfile(fileName) == False):
            header = True

        usercsv = open(fileName, 'a')

        if (header):
            usercsv.write('Time, Total Bytes, Delta Bytes, On-Peak, Off-Peak\n')

        usercsv.write('{0}, {1}, {2}, {3}, {4}\n'.format(user['Time'], user['Total Bytes'], user['Delta Bytes'], user['On-Peak'], user['Off-Peak']))
        usercsv.close()

def getUserStats(deviceLogPath, userLogPath, userMapPath, timeKey):
    """
    Go through the device logs, and add up the last row
    """
    userMap = loadUserMap(userMapPath)

    userStatsArray = []

    unknownUser = {}
    unknownUser['Name'] = 'Unknown'
    unknownUser['Time'] = timeKey
    unknownUser['Total Bytes'] = 0
    unknownUser['Delta Bytes'] = 0
    unknownUser['On-Peak'] = 0
    unknownUser['Off-Peak'] = 0

    userStatsArray.append(unknownUser)

    # Open device lig files that belong to each user

    # http://stackoverflow.com/questions/3207219/how-to-list-all-files-of-a-directory-in-python
    onlyfiles = [f for f in listdir(deviceLogPath) if isfile(join(deviceLogPath, f))]

    for devicecsv in onlyfiles:
        # get log file info

        mac = getMacFromFileName(devicecsv)
        ip = getIpFromFileName(devicecsv)

        #print('MAC = ' + mac)

        # load csv
        csv = np.genfromtxt(deviceLogPath + devicecsv, delimiter=',', dtype=long)

        #error handler

        if (len(csv) == 5):
            break

        if (csv[-1][0] != timeKey):
            print('Time key mismatch!')
            print(len(csv))
            print(csv)
            print deviceLogPath + devicecsv


        # does this MAC belong to a user?
        # yes, add the device values to the user dict
        if (userMap.has_key(mac)):
            # print(mac + ' belongs to ' + userMap[mac])

            # See if this user exists in the userStatsArray, if so, append, else create new user
            found = False
            for user in userStatsArray:
                if (user['Name'] == userMap[mac]):
                    found = True
                    user['Total Bytes'] += csv[-1][1]
                    user['Delta Bytes'] += csv[-1][2]
                    user['On-Peak'] += csv[-1][3]
                    user['Off-Peak'] += csv[-1][4]

            if (found == False):
                tmpUser = {}
                tmpUser['Name'] = userMap[mac]
                tmpUser['Time'] = timeKey
                tmpUser['Total Bytes'] = csv[-1][1]
                tmpUser['Delta Bytes'] = csv[-1][2]
                tmpUser['On-Peak'] = csv[-1][3]
                tmpUser['Off-Peak'] = csv[-1][4]
                userStatsArray.append(tmpUser)
        else:
            # print(mac + ' not found in userMap!')
            # Mac does not belong to user, add to the unknown user at index 0
            userStatsArray[0]['Total Bytes'] += csv[-1][1]
            userStatsArray[0]['Delta Bytes'] += csv[-1][2]
            userStatsArray[0]['On-Peak'] += csv[-1][3]
            userStatsArray[0]['Off-Peak'] += csv[-1][4]

    return userStatsArray

def getCommuneStats(userStats, communeLogPath, timeKey):
    """
    Loop through all user files and add their last value to commune
    """

    commune = {}
    commune['Time'] = timeKey
    commune['Total Bytes'] = 0
    commune['Delta Bytes'] = 0
    commune['On-Peak'] = 0
    commune['Off-Peak'] = 0

    for userDict in userStats:

        if (userDict['Time'] != timeKey):
            print timeKey
            print(fileName)
            print('Time key mismatch!')
            print csv

        commune['Total Bytes'] += userDict['Total Bytes']
        commune['Delta Bytes'] += userDict['Delta Bytes']
        commune['On-Peak'] += userDict['On-Peak']
        commune['Off-Peak'] += userDict['Off-Peak']

    return commune

def logCommuneStats(communeLogFile, communeStats):
    """
    Append the commune to their csv files
    """

    header = False

    if (os.path.isfile(communeLogFile) == False):
        header = True

    communecsv = open(communeLogFile, 'a')

    if (header):
        communecsv.write('Time, Total Bytes, Delta Bytes, On-Peak, Off-Peak\n')

    communecsv.write('{0}, {1}, {2}, {3}, {4}\n'.format(communeStats['Time'], communeStats['Total Bytes'], communeStats['Delta Bytes'], communeStats['On-Peak'], communeStats['Off-Peak']))
    communecsv.close()

def getIpFromFileName(name):
    result = name.split('_')
    result = str(result[1])[:-4]

    return result

def getMacFromFileName(name):
    result = name.split('_')
    result = result[0].replace('-', ':')

    return result

def initSession(username, password, session):
    auth = 'Basic ' + base64.b64encode(username + ':' + password)
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

def fixIpsInDictArray(statsDictArray):
    """Convert dec IP to nice IP"""

    newDictArray = statsDictArray

    for statsDict in newDictArray:
        statsDict['ipAddress'] = decStrToIpStr(statsDict['ipAddress'])
        statsDict['totalBytes'] = int(statsDict['totalBytes'])

    return newDictArray

def cleanStatsDictArray(statsDictArray):
    """
    Loop through dict array and remove invalid dicts

    """
    newDictArray = []

    for statsDict in statsDictArray:
        if (len(statsDict) == 12):
            newDictArray.append(statsDict)

    return newDictArray

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

def squashStatsDictArray(statsDictArray):
    """Strip extra data"""

    newDictArray = []

    for statsDict in statsDictArray:
        tmpDict = {'ipAddress': statsDict['ipAddress'],
                    'macAddress': statsDict['macAddress'],
                    'totalBytes': statsDict['totalBytes']}

        newDictArray.append(tmpDict)

    return newDictArray

def loadUserMap(path):
    """
    MAC = User
    """
    csv = np.genfromtxt(path, delimiter=", ", dtype=str)
    csv = csv[1:]

    userMap = {}
    for row in csv:
        userMap[row[1]] = row[0]

    return userMap

main()
