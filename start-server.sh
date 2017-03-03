#!/bin/bash

# HTTP server configuration
port=8000

host=0.0.0.0
serve_path=logs/2017-2
updir=../../

# Router credentials
username=admin
password=$(cat password_file)

# Python HTTP server
if [ -f http-server.pid ]; then
	echo Python HTTP server is already running!

else
	echo Starting Python HTTP server on $host:$port

	mkdir -p $serve_path
	cd $serve_path
	unbuffer python3 -m http.server $port >> ../../http-server.log 2>&1 &
	cd $updir

	echo $! > http-server.pid
	echo PID = $!
fi

# dalla-stats
if [ -f dalla-stats.pid ]; then
	echo dalla-stats is already running!
else
	echo Starting dalla-stats daemon...

	unbuffer python2 dalla-stats.py -u $username -p $password >> dalla-stats.log 2>&1 &

	echo $! > dalla-stats.pid
	echo PID = $!
fi
