#!/bin/bash

# Dirs
pidDir=/var/run
installDir=/usr/lib/dalla-stats/logger

dataLogDir=/mnt/dalla-hdd/dalla-stats/logs
mkdir -p $dataLogDir

logFile=/mnt/dalla-hdd/dalla-stats/dalla-logger.log
mkdir -p /mnt/dalla-hdd/dalla-stats

configDir=/etc/dalla-stats
mkdir -p $configDir

passwordFile=$configDir/router_key

# Dalla-Logger Config
interval=60
username=admin
password=$(cat $passwordFile)

# Router credentials

# dalla-data
if [ -f $pidDir/dalla-logger.pid ]; then
	echo dalla-logger is already running!
else
	echo Starting dalla-logger daemon...

	unbuffer python3 $installDir/dalla-logger.py -u $username -p $password -i $interval -d $dataLogDir >> $logFile 2>&1 &

	echo $! > $pidDir/dalla-logger.pid
	echo PID = $!
fi
