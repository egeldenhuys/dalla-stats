#!/bin/bash

# Install dalla-logger
sudo mkdir -p /usr/lib/dalla-stats/logger
sudo cp -f dalla-logger.py restart-server.sh stop-server.sh start-server.sh /usr/lib/dalla-stats/logger/

sudo cp -f dalla-logger.service /etc/systemd/system/dalla-logger.service
sudo systemctl enable dalla-logger.service
sudo systemctl start dalla-logger.service
