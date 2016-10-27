# Changelog

This project adheres to [Semantic Versioning](http://semver.org/).

## Unreleased

### Added

### Changed
- File paths are now hard-coded in main, instead of the separate functions #15
- Change directory structure to allow monthly captures #33
- Logging is now enabled by default
- Default interval has been set to 60 seconds
- --interval, --root-directory and --disable-logging are now optional

### Fixed
- CRTL+C losing data while waiting for router

## 0.0.4 - 2016-10-25
### Added
- Log timestamp to console when fetching records
- Now classify data has On-Peak or Off-Peak depending on timestamp of device record #3
- Create overview.csv that contains a summary for TOTAL and each USER #5
- Catches KeyboardInterrupt and does a final capture and saves to disk #12

## 0.0.3 - 2016-10-24
### Added
- Port to Python 3

### Fixed
- Handles router errors #10
- Keeps data on restart #11

## 0.0.2 - 2016-10-24
### Added
- Store a summary of the device records on disk #2, #4
- Monitor only mode (Produces no .csv for graphing) #8
- Will now place all log files in the given working directory

### Removed
- Remove graphs from README.md #13
- Remove numpy dependency (was not working on Termux)

## 0.0.1 - 2016-10-23
- Initial release
