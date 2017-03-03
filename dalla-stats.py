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


version = 'v0.2.3'

def main():

    print('[INFO] Starting Dalla-Stats ' + version)

    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--username", default='', help="the router admin username")
    parser.add_argument("-p", "--password", default='', help="the router admin password")
    parser.add_argument("-i", "--interval", type=int, default=60, help="the interval in seconds to update the log files")
    parser.add_argument("--poll-interval", type=int, default=1, help="the interval in seconds to update the statistics")
    parser.add_argument("-d", "--root-directory", default='.', help="directory to save logs")
    parser.add_argument("-l", "--disable-logging", default=False, action='store_true', help="Disable logging of statistics")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + version)

    args = parser.parse_args()

    pollInterval = args.poll_interval
    lastLog = 0

    if (args.username == '' or args.password == ''):
        print('[ERROR] Please supply username and password')
        exit()

    if (args.interval == 0):
        print('[ERROR] Interval needs to be > 0')
        exit()

    rootDir = args.root_directory

    # ===============
    # Time paramaters
    # ===============
    timeKey = int(time.time()) # UTC TIME!
    localTime = time.localtime(timeKey)

    month = localTime.tm_mon
    oldMonth = month


    day = localTime.tm_mday
    oldDay = day

    year = localTime.tm_year

    datekey = str(year) + '-' + str(month)

    dirStruct = getDirStructure(rootDir, datekey)

    # Load cache and user map
    userMap = loadUserMap(dirStruct['userMapFile'])
    oldStats = loadDeviceCache(dirStruct['cacheFile'])

    userUsageToday = loadUserUsageToday(dirStruct['userDir'])

    session = initSession(args.username, args.password)

    delta = []
    abort = False
    specialEvents = {}
    specialEvents['forceLog'] = False


    while (True):
        try:
            timeKey = int(time.time())
            localTime = time.localtime(timeKey)
            month = localTime.tm_mon
            day = localTime.tm_mday

            #print('[INFO] Getting device records @ ' + str(timeKey))

            deviceStats = getDeviceRecords(session, timeKey)

            # Only do calculations and logging if we were able to get new stats
            if (len(deviceStats) != 0):
                delta = calculateDeviceDeltas(oldStats, deviceStats, specialEvents)

                mergeDevices(oldStats, delta)

                if (oldMonth != month):
                    specialEvents['forceLog'] = True

                    print('[INFO] We have entered a new month! Resetting all statistics...')
                    year = time.localtime(timeKey).tm_year
                    oldMonth = month

                    dateKey = str(year) + '-' + str(month)
                    dirStruct = getDirStructure(rootDir, dateKey)

                    tickOver(delta)

                userStats = getUserStats(delta, userMap, timeKey)
                sortUsers(userStats)

                # NOTE: Disabled here, Nobody will see the server console
                # if (userStats[0]['Name'] == "TOTAL"):
                #     print('Delta = {0} KiB/s'.format(userStats[0]['Delta'] / 1024))

                # First run, we cannot safely say how much users have used today.
                # So set their usage to 0
                if (len(userUsageToday) == 0):
                    userUsageToday = addDeltaToUserUsageToday(userStats, userUsageToday)
                    resetRecords(userUsageToday)
                else:
                    userUsageToday = addDeltaToUserUsageToday(userStats, userUsageToday)

                if (oldDay != day):
                    specialEvents['forceLog'] = True
                    print('[INFO] We have entered a new day! Resetting daily statistics...')
                    oldDay = day

                    tickOver(userUsageToday)

                calculateTotalUsageToday(userUsageToday)
                sortUsers(userUsageToday)

                if (timeKey - lastLog >= args.interval or abort == True or specialEvents['forceLog'] == True):
                    specialEvents['forceLog'] = False
                    print('[INFO] Logging records @ ' + time.strftime('%c', time.localtime(timeKey)))

                    saveDeviceCache(delta, dirStruct['cacheFile'])
                    saveSummary(userStats, dirStruct['summaryFile'], 'html', 'Total')
                    saveSummary(userUsageToday, dirStruct['todayFile'], 'html', 'Today')

                    if (args.disable_logging == False):
                        logDeviceStats(delta, dirStruct['deviceDir'])
                        logUserStats(userStats, dirStruct['userDir'])

                    lastLog = timeKey

                oldStats = delta

            else:
                print('[ERROR] Failed to get device records from router.')
                # Getting records fail, try to logout
                # REVIEW: Does this work when timout occurs
                logout(session)

            if (abort == False):
                time.sleep(pollInterval)
            else:
                break

        except (KeyboardInterrupt, SystemExit) as e:
            print(e)
            print('\n[INFO] Exiting. Please wait...')
            time.sleep(1)
            abort = True

def resetRecords(devicesArray):

    for device in devicesArray:
        device['On-Peak'] = 0
        device['Off-Peak'] = 0
        device['Delta'] = 0

def tickOver(devicesArray):
    # Go through each device and set on and off peak counters to delta
    # Used when entering a new month and we want to forget previous On and Off peak
    # also used for enterting a new day
    # DELTA is the data in the new day/month that needs to be classified

    for device in devicesArray:
        device['On-Peak'] = 0
        device['Off-Peak'] = 0
        classifyDelta(device)

def getDirStructure(rootDir, dateKey):
    dirStruct = {}

    dirStruct['rootDir'] = rootDir
    dirStruct['userMapFile'] = rootDir + '/user-map.csv'
    dirStruct['logDir'] = rootDir + '/logs/' + str(dateKey)
    dirStruct['cacheFile'] = dirStruct['logDir'] + '/cache.csv'
    dirStruct['deviceDir'] = dirStruct['logDir'] + '/devices'
    dirStruct['userDir'] = dirStruct['logDir'] + '/users'
    dirStruct['summaryFile'] = dirStruct['logDir'] + '/total.html'
    dirStruct['totalFile'] = dirStruct['logDir'] + '/total.csv'
    dirStruct['todayFile'] = dirStruct['logDir'] + '/index.html'

    return dirStruct

def saveSummary(users, summaryFile, mode='csv', title='Today'):

    scale = 0.000000954
    scaleStr = 'MiB'
    points = 2

    timeKey = int(time.time()) # UTC TIME!
    localTime = time.localtime(timeKey)

    year = localTime.tm_year
    month = localTime.tm_mon

    totalDays = calendar.monthrange(year, month)[1]

    maxOn = -1
    maxOff = -1

    userCount = 10

    # Bytes
    if (title == "Total"):
        maxOn = float(400 * 1073741824) / userCount
        maxOff = float(1000 * 1073741824) / userCount
    elif (title == "Today"):

        maxOn = ((float(400) / totalDays) / userCount) * 1073741824
        maxOff = float(1000 * 1073741824) / totalDays / userCount

    if not os.path.exists(os.path.dirname(summaryFile)):
        os.makedirs(os.path.dirname(summaryFile))

    overviewFile = open(summaryFile, 'w')

    # TODO: Sort users based on actual total

    if (mode == 'csv'):
        overviewFile.write('Name, Total, On-Peak, Off-Peak\n')

        for userDict in users:
            overviewFile.write(userDict['Name'] + ', ' + str(userDict['On-Peak'] +
            userDict['Off-Peak']) + ', ' + str(userDict['On-Peak']) + ', ' + str(userDict['Off-Peak']) + '\n')

    elif (mode == 'txt'):

        for userDict in users:
            overviewFile.write('--------\n' + userDict['Name'] + "\n--------\n")
            overviewFile.write('Total    : ' + str((userDict['On-Peak'] + userDict['Off-Peak']) * scale) + ' ' + scaleStr + '\n')
            overviewFile.write('On-Peak  : ' + str(userDict['On-Peak'] * scale) + ' ' + scaleStr + '\n')
            overviewFile.write('Off-Peak : ' + str(userDict['Off-Peak'] * scale) + ' ' + scaleStr + '\n\n')
    elif (mode == 'html'):
        overviewFile.write('<!DOCTYPE html>\n<html>\n<head><title>Dalla Stats</title></head>\n<body>\n')

        overviewFile.write('<h1>' + title + '</h1>\n')
        overviewFile.write("<a href=/index.html>Today</a><br>\n<br>\n")
        overviewFile.write("<a href=/total.html>Total</a><br>\n")
        overviewFile.write('<p style="font-family:courier, monospace;">\n')
        overviewFile.write('version: ' + version + '<br>\n\n')

        overviewFile.write(time.strftime('%c', localTime))

        overviewFile.write('<br>\n<br>\n')

        for userDict in users:

            total = userDict['On-Peak'] + userDict['Off-Peak']
            onPeak = userDict['On-Peak']
            offPeak = userDict['Off-Peak']

            if (userDict['Name'] == 'TOTAL'):
                onPerc = round((float(onPeak) / (maxOn * userCount)) * 100, 2)
                offPerc = round((float(offPeak) / (maxOff * userCount)) * 100, 2)
            else:
                onPerc = round(float(onPeak) / maxOn)
                onPerc = round((float(onPeak) / maxOn) * 100, 2)
                offPerc = round((float(offPeak) / maxOff) * 100, 2)

            overviewFile.write('=======<br>\n' + userDict['Name'] + "<br>\n=======<br>\n")
            overviewFile.write('Total    : ' + str(round(total * scale, points)) + ' ' + scaleStr + '<br>\n')
            overviewFile.write('On-Peak  : ' + str(round(onPeak * scale, points)) + ' ' + scaleStr)
            overviewFile.write(' (' + str(onPerc) + '%)<br>\n')
            overviewFile.write('Off-Peak : ' + str(round(offPeak * scale, points)) + ' ' + scaleStr)
            overviewFile.write(' (' + str(offPerc) + '%)<br>\n<br>\n')

        overviewFile.write('</p>\n</body>\n</html>')

    overviewFile.close()

def saveDeviceCache(deviceStatsArray, cacheFile):
    """Save the given dict array to file
    """

    if (not os.path.exists(os.path.dirname(cacheFile))):
        os.makedirs(os.path.dirname(cacheFile))

    output = open(cacheFile, 'w')

    output.write('MAC Address, IP Address, Time,Total Bytes, Delta, On-Peak, Off-Peak\n')

    for device in deviceStatsArray:
        output.write('{0}, {1}, {2}, {3}, {4}, {5}, {6}\n'.format(device['MAC Address'],
        device['IP Address'], device['Time'], device['Total Bytes'], device['Delta'],
        device['On-Peak'], device['Off-Peak']))

    output.close()

def loadDeviceCache(cacheFile):
    """Load the device summary into a dict array
    """

    """
    MAC Address, IP Address, Time, Total Bytes, Delta, On-Peak, Off-Peak
    """

    print('[INFO] Loading device cache from {0}'.format(cacheFile))

    deviceStats = []

    if (os.path.isfile(cacheFile) == False):
        return []

    inputFile = open(cacheFile, 'r')
    reader = csv.reader(inputFile, delimiter=',', skipinitialspace=True)

    for row in reader:
        if (reader.line_num != 1):
            tmpDevice = {}

            tmpDevice['MAC Address'] = row[0]
            tmpDevice['IP Address'] = row[1]
            tmpDevice['Time'] = int(row[2])
            tmpDevice['Total Bytes'] = int(row[3])
            tmpDevice['Delta'] = int(row[4])
            tmpDevice['On-Peak'] = int(row[5])
            tmpDevice['Off-Peak'] = int(row[6])

            deviceStats.append(tmpDevice)

    inputFile.close()

    return deviceStats

def mergeDevices(oldDevices, newDevices):
    """
    When a device is removed from the router we do not want to lose track of it
    """

    # Go through all the old devices
    # If it was not found in the newDevices, add it, and flag it

    tmpAdd = []

    for old in oldDevices:
        # Does it exist in newDevices?
        found = False
        for new in newDevices:
            if (old['MAC Address'] == new['MAC Address']):
                if (old['IP Address'] == new['IP Address']):
                    found = True

        if (found == False):
            tmpAdd.append(old)

    # Go through each device record that not longer exists on the router
    for add in tmpAdd:
        if (not 'DO_NOT_LOG' in add):
            # Flag this device as it was not found on the router
            # So we do not want to add a duplicate entry in the log file
            # This flag will only be present in the mergeDevices if not found
            # Otherwise this flag will not be merged
            add['DO_NOT_LOG'] = True

            # CHANGED: Reset byte buffer when device has been removed from router
            add['Total Bytes'] = 0
            add['Delta'] = 0
            print('==================================================================')
            print('[WARN] Device was not found on router. Reset Total Bytes and Delta:')
            print('-----------------------------------------------------------------')
            print(add)
            print('-----------------------------------------------------------------')
            print('')

        newDevices.append(add)

def initDevices(statsDictArray, timeKey):
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
                        'Time': timeKey,
                        'Delta': -9999999999,
                        'On-Peak': -9999999999,
                        'Off-Peak': -9999999999}

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
        print('[ERROR] Failed to get device records from router!')
        if (r.text == '<html><head><title>500 Internal Server Error</title></head><body><center><h1>500 Internal Server Error</h1></center></body></html>'):
            print('\t Another admin has logged in!')
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
    init = initDevices(dictArray, timeKey)

    logout(session)

    return init

def classifyDelta(deviceDict):
    """Given a device record, classift the delta
    """

    # init values
    if (deviceDict['On-Peak'] < 0):
        deviceDict['On-Peak'] = 0

    if (deviceDict['Off-Peak'] < 0):
        deviceDict['Off-Peak'] = 0

    localTime = time.localtime(deviceDict['Time'])

    if (localTime.tm_hour < 6):
        deviceDict['Off-Peak'] = deviceDict['Off-Peak'] + deviceDict['Delta']
    else:
        deviceDict['On-Peak'] = deviceDict['On-Peak'] + deviceDict['Delta']

def calculateDeviceDeltas(oldDeviceDeltas, currentDeviceRecords, specialEvents={}):

    localCurrent = currentDeviceRecords

    # Go through each new device entry
    for newDeviceDict in localCurrent:

        # search for matching device in old devices
        found = False

        for oldDeviceDict in oldDeviceDeltas:

            # look for match
            if (oldDeviceDict['MAC Address'] == newDeviceDict['MAC Address']):
                if (oldDeviceDict['IP Address'] == newDeviceDict['IP Address']):
                    found = True

                    # Historic device
                    if (oldDeviceDict['Time'] == newDeviceDict['Time']):
                        break

                    # Inherit counters
                    newDeviceDict['On-Peak'] = oldDeviceDict['On-Peak']
                    newDeviceDict['Off-Peak'] = oldDeviceDict['Off-Peak']

                    newDeviceDict['Delta'] = newDeviceDict['Total Bytes'] - oldDeviceDict['Total Bytes']

                    if (newDeviceDict['Delta'] < 0):
                        specialEvents['forceLog'] = True
                        print('=================================')
                        print('[WARN] Device has negative delta!')
                        print('Delta = ' + str(newDeviceDict['Delta']))
                        print('---------------------------------')
                        newDeviceDict['Delta'] = newDeviceDict['Total Bytes']
                        print('-----------')
                        print('Old record:')
                        print('-----------')
                        print(oldDeviceDict)
                        print('-----------')
                        print('New record:')
                        print('-----------')
                        print(newDeviceDict)
                        print('---------------------------------')
                        print('')

                    classifyDelta(newDeviceDict)

        # No matching old dict was found
        if (found == False):
            print('[INFO] New device found:')

            newDeviceDict['Delta'] = newDeviceDict['Total Bytes']
            classifyDelta(newDeviceDict)

            print(newDeviceDict)
            print('')

    return localCurrent

def logDeviceStats(statsDictArray, deviceDir):
    """Save device dict array to log files
    """
    """
    filename: M-A-C_I.P
    Time, Total Bytes, Delta, On-Peak, Off-Peak
    """

    if (not os.path.exists(deviceDir)):
        os.makedirs(deviceDir)

    for statsDict in statsDictArray:

        if (not 'DO_NOT_LOG' in statsDict):
            # Generate file name
            mac = statsDict['MAC Address'].replace(':', '-')
            ip = statsDict['IP Address']
            fileName = str(deviceDir + '/' + mac + '_' + ip + '.csv')

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

def addToUser(src, dst):
    dst['Total Bytes'] += src['Total Bytes']
    dst['Delta'] += src['Delta']
    dst['On-Peak'] += src['On-Peak']
    dst['Off-Peak'] += src['Off-Peak']

def getUserStats(deviceStatsArray, userMap, timeKey):
    """ Go through the device dict array and add up all values
    that belong to each user
    """

    #timeKey = int(time.time())

    userStatsArray = []

    # Create the default user 0
    unknownUser = {}
    unknownUser['Name'] = 'UNKNOWN'
    unknownUser['Time'] = timeKey
    unknownUser['Total Bytes'] = 0
    unknownUser['Delta'] = 0
    unknownUser['On-Peak'] = 0
    unknownUser['Off-Peak'] = 0

    totalUser = {}
    totalUser['Name'] = 'TOTAL'
    totalUser['Time'] = timeKey
    totalUser['Total Bytes'] = 0
    totalUser['Delta'] = 0
    totalUser['On-Peak'] = 0
    totalUser['Off-Peak'] = 0

    # Open each device and determine to who it beints
    for deviceDict in deviceStatsArray:
        # Get Device info
        mac = deviceDict['MAC Address']
        ip = deviceDict['IP Address']

        if (deviceDict['Time'] != timeKey and (not 'DO_NOT_LOG' in deviceDict)):
            print('==================================================')
            print('[ERROR] Time key mismatch while getting user stats:')
            print('--------------------------------------------------')
            print('Given timeKey = {0}'.format(timeKey))
            print('Device timeKey = {0}'.format(deviceDict['Time']))
            print('--------------------------------------------------')

        # Use usermap to determine to who this mac beints
        if (mac in userMap):

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
                    break

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
            addToUser(deviceDict, unknownUser)

        addToUser(deviceDict, totalUser)

    userStatsArray.append(totalUser)
    userStatsArray.append(unknownUser)

    return userStatsArray

def logUserStats(userStatsArray, userDir):
    """
    Append the user data to their csv files
    """

    if (not os.path.exists(userDir)):
        os.makedirs(userDir)

    for user in userStatsArray:
        fileName = userDir + '/' + user['Name'] + '.csv'
        header = False

        if (os.path.isfile(fileName) == False):
            header = True

        usercsv = open(fileName, 'a')

        if (header):
            usercsv.write('Time, Total Bytes, Delta, On-Peak, Off-Peak\n')

        usercsv.write('{0}, {1}, {2}, {3}, {4}\n'.format(user['Time'], user['Total Bytes'], user['Delta'], user['On-Peak'], user['Off-Peak']))
        usercsv.close()

def getTotalStats_DEPRECATED(userStats):
    """
    Loop through all user dicts and add their last value to total
    """

    timeKey = int(time.time())

    total = {}
    total['Time'] = timeKey
    total['Total Bytes'] = 0
    total['Delta'] = 0
    total['On-Peak'] = 0
    total['Off-Peak'] = 0

    for userDict in userStats:

        # if (userDict['Time'] != timeKey):
        #     print('[WARN] Time key mismatch! (getTotalStats)')
        if (userDict['Name'] != 'TOTAL'):
            total['Total Bytes'] += userDict['Total Bytes']
            total['Delta'] += userDict['Delta']
            total['On-Peak'] += userDict['On-Peak']
            total['Off-Peak'] += userDict['Off-Peak']

    return total

def logTotalStats(totalStats, totalFile):
    """
    Append the total to their csv files
    """

    if (not os.path.exists(os.path.dirname(totalFile))):
        os.makedirs(os.path.dirname(totalFile))

    header = False

    if (os.path.isfile(totalFile) == False):
        header = True

    totalcsv = open(totalFile, 'a')
    if (header):
        totalcsv.write('Time, Total Bytes, Delta, On-Peak, Off-Peak\n')

    totalcsv.write('{0}, {1}, {2}, {3}, {4}\n'.format(totalStats['Time'], totalStats['Total Bytes'], totalStats['Delta'], totalStats['On-Peak'], totalStats['Off-Peak']))
    totalcsv.close()

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

def loadUserMap(userMapFile):
    """
    MAC, User
    """
    print('[INFO] Loading User-Map from ' + userMapFile)

    userMap = {}

    if (os.path.isfile(userMapFile) == False):
        return userMap

    inputFile = open(userMapFile)
    reader = csv.reader(inputFile, delimiter=',', skipinitialspace=True)

    for row in reader:
        if (reader.line_num != 1):
            userMap[row[1]] = row[0]

    inputFile.close()

    return userMap

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
        print(str(datetime.datetime.now()) + ' [ERROR] Unexpected error: ', sys.exc_info()[0])
        return


    if (r.text != '[cgi]0\n[error]0'):
        print('[ERROR] Logout failed:')

        if (r.text == '<html><head><title>500 Internal Server Error</title></head><body><center><h1>500 Internal Server Error</h1></center></body></html>'):
            print('\t Another admin has logged in!')
        else:
            print('\t' + r.text)

def getUserUsageToday_PLOT_OLD(userDir):
    """
    Load every user, but only add the values that fall within today

    REQUIRES -l
    REQUIRES intact .csv records for users
    """

    userArray = []

    timeKey = time.time()
    today = time.localtime(timeKey).tm_mday

    if (not os.path.exists(userDir)):
        return []

    fileList = [f for f in listdir(userDir) if isfile(join(userDir, f))]

    for userFile in fileList:
        userName = userFile[:-4] # Trim .csv
        tmpUser = {}
        tmpUser['Name'] = userName
        tmpUser['Total'] = 0
        tmpUser['On-Peak'] = 0
        tmpUser['Off-Peak'] = 0

        # Collect today's records
        with open(userDir + '/' + userFile, 'r') as csvfile:
            inputFile = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
            inputFile.next()

            for row in inputFile:
                recordTimeKey = int(row[0])
                recordDay = time.localtime(recordTimeKey).tm_mday

                if (recordDay == today):
                    tmpUser['Total'] = tmpUser['Total'] + int(row[3]) + int(row[4])
                    tmpUser['On-Peak'] = tmpUser['On-Peak'] + int(row[3])
                    tmpUser['Off-Peak'] = tmpUser['Off-Peak'] + int(row[4])

        userArray.append(tmpUser)

    return userArray

def calculateTotalUsageToday(userUsageToday):
    total = {}
    total['On-Peak'] = 0
    total['Off-Peak'] = 0

    for u in userUsageToday:
        if (u['Name'] != 'TOTAL'):
            total['On-Peak'] = total['On-Peak'] + u['On-Peak']
            total['Off-Peak'] = total['Off-Peak'] + u['Off-Peak']

    for u in userUsageToday:
        if (u['Name'] == 'TOTAL'):
            u['On-Peak'] = total['On-Peak']
            u['Off-Peak'] = total['Off-Peak']

def loadUserUsageToday(userDir):
    """
    Last - First = Today

    REQUIRES -l
    REQUIRES intact .csv records for users
    """

    print('[INFO] Loading daily user usage from ' + userDir)

    userArray = []

    timeKey = time.time()
    today = time.localtime(timeKey).tm_mday

    if (not os.path.exists(userDir)):
        return []

    fileList = [f for f in listdir(userDir) if isfile(join(userDir, f))]

    for userFile in fileList:
        userName = userFile[:-4] # Trim .csv
        tmpUser = {}
        tmpUser['Name'] = userName
        tmpUser['Total'] = 0
        tmpUser['On-Peak'] = 0
        tmpUser['Off-Peak'] = 0

        # Collect today's records
        with open(userDir + '/' + userFile, 'r') as csvfile:
            foundFirst = False
            foundLast = False
            totalLines = 0

            first = [0, 0, 0]
            last = [0, 0, 0]

            inputFile = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
            inputFile.next()

            for row in inputFile:
                recordTimeKey = int(row[0])
                recordDay = time.localtime(recordTimeKey).tm_mday

                if (recordDay == today and foundFirst == False):
                    foundFirst = True
                    first = [int(row[3]), int(row[4]), int(row[3]) + int(row[4])]


                if (recordDay != today and foundFirst == True):
                    foundLast = True
                    last = [int(row[3]), int(row[4]), int(row[3]) + int(row[4])]
                    break

                last = [int(row[3]), int(row[4]), int(row[3]) + int(row[4])]

            tmpUser['On-Peak'] = last[0] - first[0]
            tmpUser['Off-Peak'] = last[1] - first[1]
            tmpUser['Total'] = last[2] - first[2]

        userArray.append(tmpUser)

    return userArray

def logUsageToday_OLD(userUsageToday, dailyUsageFile):
    print('[DEBUG] Logging Usage for today')

    if (not os.path.exists(os.path.dirname(dailyUsageFile))):
        os.makedirs(os.path.dirname(dailyUsageFile))

    total = {}
    total['On-Peak'] = 0
    total['Off-Peak'] = 0

    for u in users:
        total['On-Peak'] = total['On-Peak'] + u['On-Peak']
        total['Off-Peak'] = total['Off-Peak'] + u['Off-Peak']

    saveSummary(users, total, dailyUsageFile, 'html')

def addDeltaToUserUsageToday(currentUsers, userUsageToday):
    # print('[DEBUG] Adding delta to daily user usage records')

    # Go through each new user record
    for userDelta in currentUsers:

        # search for matching device in old devices
        found = False

        for userToday in userUsageToday:

            # look for match
            if (userDelta['Name'] == userToday['Name']):
                found = True
                userToday['Time'] = userDelta['Time']
                userToday['Delta'] = userDelta['Delta']

                classifyDelta(userToday)

        # No matching old dict was found
        if (found == False):
            print('---------------------------------------------')
            print('[INFO] Adding new user to Daily Usage Records')

            userToday = userDelta.copy()

            userToday['On-Peak'] = 0
            userToday['Off-Peak'] = 0
            classifyDelta(userToday)

            userUsageToday.append(userToday)

            print(userToday)

            print('---------------------------------------------\n')

    return userUsageToday

def sortUsers(users):

    # take a user from the array
    for j in range(0, len(users)):
        for i in range(0, len(users) - 1):
            if (users[i]['On-Peak'] + users[i]['Off-Peak'] < users[i + 1]['On-Peak'] + users[i + 1]['Off-Peak']):
                # swap
                tmp = users[i]
                users[i] = users[i + 1]
                users[i + 1] = tmp

main()
