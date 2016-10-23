"""
Process:

Load all device csv logs from directory
-> array of dicts containing last line from csv [OLD]
    Time, Total Bytes, Delta, On-Peak, Off-Peak

Get new device stats from router
-> dict array [NEW]
    Time, Total Bytes

Calculate Delta given old and new device stats
-> New stats get new keys
    Delta, On-Peak, Off-Peak

Append new stats to log file
-> write new stats to their corresponding csv

Get user stats from device stats array
Add up all fields from corresponding devices for each user
-> Dict array of users
    Time, Total Bytes, Delta, On-Peak, Off-Peak

Append user stats to log files
-> write new stats to their corresponding csv

Get commune stats
-> Add up all user fields
return dict

Log commune stats
-> append dict to commune log files

oldStats = newStats
wait some time, then repeat

"""
import argparse
import requests
import base64
import time
import os
import numpy as np
from os import listdir
from os.path import isfile, join

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="the router admin username")
    parser.add_argument("-p", "--password", help="the router admin password")
    parser.add_argument("-i", "--interval", type=int, help="the interval in seconds to update the statistics")
    parser.add_argument("-d", "--device-log-dir", help="the folder to store device log files")
    parser.add_argument("-e", "--user-log-dir", help="the folder to store user log files")
    parser.add_argument("-c", "--commune-log-file", help="the path of the commune log file")
    parser.add_argument("-m", "--user-map-file", help="the path of the user map .csv")
    args = parser.parse_args()

    oldDeviceStats = loadDeviceStats(args.device_log_dir)
    userStats = []

    userMap = loadUserMap(args.user_map_file)

    session = requests.session()
    initSession(args.username, args.password, session)

    while (True):
        print('Get stats...')

        timeKey = int(time.time())

        deviceStats = getDeviceStats(session, timeKey)

        if (len(oldDeviceStats) == 0):
            oldDeviceStats = deviceStats

        if (len(oldDeviceStats) > len(deviceStats)):
            print('Old device count > new device count!')
            # Need to merge old and new
            
        deviceStats = updateDeviceStats(oldDeviceStats, deviceStats, timeKey, args.device_log_dir)
        logDeviceStats(args.device_log_dir, deviceStats)

        userStats = getUserStats(deviceStats, userMap, timeKey)
        logUserStats(args.user_log_dir, userStats)

        communeStats = getCommuneStats(userStats, args.commune_log_file, timeKey)
        logCommuneStats(args.commune_log_file, communeStats)

        oldDeviceStats = deviceStats
        time.sleep(args.interval)

def loadDevice(deviceLogDir, macAddress, ipAddress):

    """ Open each csv file in the log dir
    and load the last line into the device dict array
    """

    try:
        os.mkdir(deviceLogDir)
    except OSError:
        i = 5

    # Generate file name
    mac = macAddress.replace(':', '-')
    ip = ipAddress
    fileName = str(deviceLogDir + mac + '_' + ip + '.csv')

    if (os.path.isfile(fileName) == False):
        none = {}
        return none

    # load device csv
    csv = np.genfromtxt(fileName, delimiter=',', dtype=long)

    # populate device dict
    tmpDevice = {}
    tmpDevice['Time'] = csv[-1][0]
    tmpDevice['MAC Address'] = mac
    tmpDevice['IP Address'] = ip
    tmpDevice['Total Bytes'] = csv[-1][1]
    tmpDevice['Delta'] = csv[-1][2]
    tmpDevice['On-Peak'] = csv[-1][3]
    tmpDevice['Off-Peak'] = csv[-1][4]

    return tmpDevice

def loadDeviceStats(deviceLogDir):
    """ Open each csv file in the log dir
    and load the last line into the device dict array
    """

    deviceStatsArray = []

    try:
        os.mkdir(deviceLogDir)
    except OSError:
        i = 5

    onlyfiles = [f for f in listdir(deviceLogDir) if isfile(join(deviceLogDir, f))]

    for devicecsv in onlyfiles:
        # Extract info from log files
        mac = getMacFromFileName(devicecsv)
        ip = getIpFromFileName(devicecsv)

        # load device csv
        csv = np.genfromtxt(deviceLogDir + devicecsv, delimiter=',', dtype=long)

        # populate device dict
        tmpDevice = {}
        tmpDevice['Time'] = csv[-1][0]
        tmpDevice['MAC Address'] = mac
        tmpDevice['IP Address'] = ip
        tmpDevice['Total Bytes'] = csv[-1][1]
        tmpDevice['Delta'] = csv[-1][2]
        tmpDevice['On-Peak'] = csv[-1][3]
        tmpDevice['Off-Peak'] = csv[-1][4]

        # add device dict to array
        deviceStatsArray.append(tmpDevice)

    return deviceStatsArray

def getDeviceStats(session, timeKey):
    """Given a valid session, scrape the device stats from the router
    """

    # Configure page specific headers
    url = 'http://192.168.1.1/cgi?1&5'
    session.headers.update({'Referer': 'http://192.168.1.1/mainFrame.htm'})
    data ='[STAT_CFG#0,0,0,0,0,0#0,0,0,0,0,0]0,0\r\n[STAT_ENTRY#0,0,0,0,0,0#0,0,0,0,0,0]1,0\r\n'

    r = session.post(url=url, data=data)
    rawStats = r.text

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
    cleaned = cleanDeviceDictArray(dictArray, timeKey)

    return cleaned

def updateDeviceStats(prevStats, newStats, timeKey, deviceLogDir):
    """Given old and new stats, calculate Delta, On-Peak, and Off-Peak
    """

    """newStats[]:
    IP Address
    MAC Address
    Total Bytes
    """

    """oldStats[]:
    Time
    IP Address
    MAC Address
    Total Bytes
    Delta
    On-Peak
    Off-Peak
    """

    """resultStats[]:
    Time
    IP Address
    MAC Address
    Total Bytes
    Delta
    On-Peak
    Off-Peak
    """

    """ Problem:
    when records deleted from router
    we lost track of the old objects

    When we see that old is now > new
    we need to calculate user and commune for old as well
    """
    # Go through each new device entry
    for newDeviceDict in newStats:
        newDeviceDict['Time'] = timeKey

        # search for matching device in old devices
        found = False
        for oldDeviceDict in prevStats:
            # look for match
            if (oldDeviceDict['MAC Address'] == newDeviceDict['MAC Address']):
                if (oldDeviceDict['IP Address'] == newDeviceDict['IP Address']):
                    found = True

                    # We are on the first run, init values
                    if (oldDeviceDict['Time'] == newDeviceDict['Time']):
                        newDeviceDict['Delta'] = 0
                        newDeviceDict['On-Peak'] = newDeviceDict['Total Bytes']
                        newDeviceDict['Off-Peak'] = 0
                    else:
                        newDeviceDict['Delta'] = newDeviceDict['Total Bytes'] - oldDeviceDict['Total Bytes']

                        if (newDeviceDict['Delta'] < 0):
                            newDeviceDict['Delta'] = newDeviceDict['Total Bytes']
                            print 'Negative delta!'

                        # TODO: Categorise Peak and off peak
                        newDeviceDict['On-Peak'] = newDeviceDict['Delta'] + oldDeviceDict['On-Peak']
                        newDeviceDict['Off-Peak'] = 0

        # No matching old dict was found
        # Need to initialize the values
        if (found == False):
            print('No prev dict found for: ')
            print(newDeviceDict)

            print('Loading from csv...')
            old = loadDevice(deviceLogDir, newDeviceDict['MAC Address'], newDeviceDict['IP Address'])

            if (len(old) == 0):
                print('Creating new record')
                newDeviceDict['Delta'] = 0
                newDeviceDict['On-Peak'] = newDeviceDict['Total Bytes']
                newDeviceDict['Off-Peak'] = 0
            else:
                print('csv found!')
                newDeviceDict['Delta'] = newDeviceDict['Total Bytes'] - old['Total Bytes']

                if (newDeviceDict['Delta'] < 0):
                    newDeviceDict['Delta'] = newDeviceDict['Total Bytes']
                    print 'Negative delta!'

                # TODO: Categorise Peak and off peak
                newDeviceDict['On-Peak'] = newDeviceDict['Delta'] + old['On-Peak']
                newDeviceDict['Off-Peak'] = 0

    updatedDeviceStats = newStats
    return updatedDeviceStats

def logDeviceStats(prefix, statsDictArray):
    """Save device dict array to log files
    """
    """
    filename: M-A-C_I.P
    Time, Total Bytes, Delta, On-Peak, Off-Peak
    """

    try:
        os.mkdir(prefix)
    except OSError:
        i = 5

    for statsDict in statsDictArray:
        # Generate file name
        mac = statsDict['MAC Address'].replace(':', '-')
        ip = statsDict['IP Address']
        fileName = str(prefix + mac + '_' + ip + '.csv')

        # csv fields
        timeKey = statsDict['Time']
        totalBytes = statsDict['Total Bytes']
        delta = statsDict['Delta']
        peak = statsDict['On-Peak']
        offPeak = statsDict['Off-Peak']

        # new device, set up csv for it
        header = False

        if (os.path.isfile(fileName) == False):
            header = True

        output = open(fileName, 'a')

        if (header):
            output.write('Time, Total Bytes, Delta, On-Peak, Off-Peak\n')

        output.write('{0}, {1}, {2}, {3}, {4}\n'.format(timeKey, totalBytes, delta, peak, offPeak))
        output.close()

def getUserStats(deviceStatsArray, userMap, timeKey):
    """ Go through the device dict array and add up all values
    that belong to each user
    """

    userStatsArray = []

    # Create the default user
    unknownUser = {}
    unknownUser['Name'] = 'Unknown'
    unknownUser['Time'] = timeKey
    unknownUser['Total Bytes'] = 0
    unknownUser['Delta'] = 0
    unknownUser['On-Peak'] = 0
    unknownUser['Off-Peak'] = 0

    userStatsArray.append(unknownUser)

    # Open each device and determine to who it belongs
    for deviceDict in deviceStatsArray:
        # Get Device info
        mac = deviceDict['MAC Address']
        ip = deviceDict['IP Address']

        if (deviceDict['Time'] != timeKey):
            print('Time key mismatch!')

        # Use usermap to determine to who this mac belongs
        if (userMap.has_key(mac)):

            # Have we seen this user before?
            found = False
            for user in userStatsArray:
                # If we have seen before, add the values to existing values
                if (user['Name'] == userMap[mac]):
                    user['Total Bytes'] += deviceDict['Total Bytes']
                    user['Delta'] += deviceDict['Delta']
                    user['On-Peak'] += deviceDict['On-Peak']
                    user['Off-Peak'] += deviceDict['Off-Peak']
                    found = True

            # If we have not seen this user before, create the user and set the values
            if (found == False):
                tmpUser = {}
                tmpUser['Name'] = userMap[mac]
                tmpUser['Time'] = timeKey
                tmpUser['Total Bytes'] = deviceDict['Total Bytes']
                tmpUser['Delta'] = deviceDict['Delta']
                tmpUser['On-Peak'] = deviceDict['On-Peak']
                tmpUser['Off-Peak'] = deviceDict['Off-Peak']
                userStatsArray.append(tmpUser)

        # if the mac was not found the the userMap, add it to Unknown user
        else:
            userStatsArray[0]['Total Bytes'] += deviceDict['Total Bytes']
            userStatsArray[0]['Delta'] += deviceDict['Delta']
            userStatsArray[0]['On-Peak'] += deviceDict['On-Peak']
            userStatsArray[0]['Off-Peak'] += deviceDict['Off-Peak']

    return userStatsArray

def logUserStats(userLogPath, userStatsArray):
    """
    Append the user data to their csv files
    """

    try:
        os.mkdir(userLogPath)
    except OSError:
        i = 5


    for user in userStatsArray:
        fileName = userLogPath + user['Name'] + '.csv'
        header = False

        if (os.path.isfile(fileName) == False):
            header = True

        usercsv = open(fileName, 'a')

        if (header):
            usercsv.write('Time, Total Bytes, Delta, On-Peak, Off-Peak\n')

        usercsv.write('{0}, {1}, {2}, {3}, {4}\n'.format(user['Time'], user['Total Bytes'], user['Delta'], user['On-Peak'], user['Off-Peak']))
        usercsv.close()

def getCommuneStats(userStats, communeLogPath, timeKey):
    """
    Loop through all user dicts and add their last value to commune
    """

    commune = {}
    commune['Time'] = timeKey
    commune['Total Bytes'] = 0
    commune['Delta'] = 0
    commune['On-Peak'] = 0
    commune['Off-Peak'] = 0

    for userDict in userStats:

        if (userDict['Time'] != timeKey):
            print timeKey
            print(fileName)
            print('Time key mismatch!')
            print csv

        commune['Total Bytes'] += userDict['Total Bytes']
        commune['Delta'] += userDict['Delta']
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
        communecsv.write('Time, Total Bytes, Delta, On-Peak, Off-Peak\n')

    communecsv.write('{0}, {1}, {2}, {3}, {4}\n'.format(communeStats['Time'], communeStats['Total Bytes'], communeStats['Delta'], communeStats['On-Peak'], communeStats['Off-Peak']))
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

def loadUserMap(path):
    """
    MAC, User
    """
    csv = np.genfromtxt(path, delimiter=", ", dtype=str)
    csv = csv[1:]

    userMap = {}
    for row in csv:
        userMap[row[1]] = row[0]

    return userMap

def cleanDeviceDictArray(statsDictArray, timeKey):
    """Strip invalid entries and parse valid entries
    """

    newDictArray = []

    for statsDict in statsDictArray:
        # Skip invalid intries
        if (len(statsDict) == 12):
            # Strip extra data,
            # Convert Dev IP to readable IP
            tmpDict = {'IP Address': decStrToIpStr(statsDict['ipAddress']),
                        'MAC Address': statsDict['macAddress'],
                        'Total Bytes': long(statsDict['totalBytes']),
                        'Time': timeKey,
                        'Delta': -9999999999,
                        'On-Peak': -9999999999,
                        'Off-Peak': -9999999999}

            newDictArray.append(tmpDict)

    return newDictArray

main()
