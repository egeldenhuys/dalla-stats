# Changelog

This project adheres to [Semantic Versioning](http://semver.org/).

## Unreleased

### Added
- Summary is now ranked from highest to lowest total usage #46
- Percentage of data used is now displayed next to each user #35

### Changed
- TOTAL is now a user #23
- User 'Unkown' has been renamed to 'UNKNOWN'. File needs to be renamed as well!

### Fixed
- Daily usage will now be correct on first run.

## v0.1.2 - 2016-10-29
## Fixed
- Day will now increment refresh when it is a new day

## v0.1.1 - 2016-10-29
### Fixed
- Will now reset the daily statistics when a new day starts

## v0.1.0 - 2016-10-29
### Added
- Reset usage when a new month begins and start a new log folder #16
- Reset byte buffer when device not found on router #30
- Produces HTML Total, and Today pages #36, #24, #17

### Changed
- File paths are now hard-coded in main, instead of in the separate functions #15
- Detailed log when negative delta #28
- Change directory structure to allow monthly captures #33
- Logging is now enabled by default
- Default interval has been set to 60 seconds
- --interval, --root-directory and --disable-logging are now optional
- Better WARN log style

### Fixed
- CRTL+C losing data while waiting for router
- Not logging out when failling to get records from router #44

## 0.0.5 - 2016-10-27
### Fixed
- Duplicate log entries when device not found on router #41

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
