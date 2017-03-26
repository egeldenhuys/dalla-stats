#!/bin/bash
pidDir=/var/run

# dalla-data
if [ ! -f $pidDir/dalla-logger.pid ]; then
	echo "dalla-data is not running (PID file not found)!"

else
	dallaPID=$(cat $pidDir/dalla-logger.pid)
	echo Killing dalla-logger daemon with PID $dallaPID
	kill -SIGINT $dallaPID
	rm $pidDir/dalla-logger.pid
fi
