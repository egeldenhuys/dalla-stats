#!/bin/bash

# HTTP server
if [ ! -f http-server.pid ]; then
	echo "HTTP server is not running (PID file not found)!"

else
	pythonHttpPID=$(cat http-server.pid)
	echo Killing HTTP server with PID $pythonHttpPID
	kill -9 $pythonHttpPID
	rm http-server.pid
fi

# dalla-stats
if [ ! -f dalla-stats.pid ]; then
	echo "dalla-stats is not running (PID file not found)!"

else
	dallaPID=$(cat dalla-stats.pid)
	echo Killing dalla-stats daemon with PID $dallaPID
	kill -9 $dallaPID
	rm dalla-stats.pid
fi
