# Dalla Stats ![](https://img.shields.io/github/release/egeldenhuys/dalla-stats.svg)

Scrape traffic statistics from TP-LINK AC750 Archer C20 Router

## Usage
```
usage: dalla-stats.py [-h] [-u USERNAME] [-p PASSWORD] [-i INTERVAL]
                      [-d WORKING_DIRECTORY] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        the router admin username
  -p PASSWORD, --password PASSWORD
                        the router admin password
  -i INTERVAL, --interval INTERVAL
                        the interval in seconds to update the statistics.
  -d WORKING_DIRECTORY, --working-directory WORKING_DIRECTORY
                        directory to save logs
  -l, --enable-logging  Log statistics?

```

## Features
- Records device, user, and total traffic usage from router
- Produces .csv for each device, user and total
    - Adds record to csv at each interval to allow for generation of graphs
    - Format: `Time, Total Bytes, Delta, On-Peak, Off-Peak`
- Associates devices with users by MAC address

## Planned Features
- [ ] Throttle user once they reach their quota
- [ ] Web interface to view current traffic usage
- [ ] Classify traffic as On-Peak and Off-Peak
- [ ] Purge log files after certain time, keeping summary intact
- [X] Real-time only mode (Produces no .csv for graphs)
- [ ] Alerts when user reaches certain quota
- [ ] Produce a human readable summary
- [ ] Handle invalid router responses (invalid password, etc)
- [ ] Better logging to stdout
