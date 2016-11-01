# Changelog

This project adheres to [Semantic Versioning](http://semver.org/).

## Unreleased

## [0.2.3] - 2016-11-01
### Fixed
- Remove testing code breaking normal functionality

## [0.2.2] - 2016-10-31 [YANKED]
### Fixed
- Fix crash when new day starts #51

## [0.2.1] -2016-10-31
### Added
- Force logging when new day starts #50

## [0.2.0] - 2016-10-31
### Added
- Ability to output Delta per second to console/log file (Disabled) #31
- Summary is now ranked from highest to lowest total usage #46
- Percentage of data used is now displayed next to each user #35

### Changed
- Poll for new records every 1 second (better accuracy of records), and write logs at --interval seconds #38
- If the log and poll interval are not the same, then the Delta in the log files
is no longer accurate and should not be sued for calculations
- Human readable timestamp when logging the get records function
- TOTAL is now a user #23
- User 'Unkown' has been renamed to 'UNKNOWN'. File needs to be renamed as well!

### Fixed
- Daily stats now start at 0 if it is the first run

## [0.1.2+dev.1] - 2016-10-30
### Added
- Summary is now ranked from highest to lowest total usage #46
- Percentage of data used is now displayed next to each user #35

### Changed
- TOTAL is now a user #23
- User 'Unkown' has been renamed to 'UNKNOWN'. File needs to be renamed as well!

### Fixed
- Daily usage will now be correct on first run.

## [0.1.2] - 2016-10-29
## Fixed
- Day will now increment when it is a new day

## [0.1.1] - 2016-10-29
### Fixed
- Reset the daily statistics when a new day starts

## [0.1.0] - 2016-10-29
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

## [0.0.5] - 2016-10-27
### Fixed
- Duplicate log entries when device not found on router #41

## [0.0.4] - 2016-10-25
### Added
- Log timestamp to console when fetching records
- Now classify data has On-Peak or Off-Peak depending on timestamp of device record #3
- Create overview.csv that contains a summary for TOTAL and each USER #5
- Catches KeyboardInterrupt and does a final capture and saves to disk #12

## [0.0.3] - 2016-10-24
### Added
- Port to Python 3

### Fixed
- Handles router errors #10
- Keeps data on restart #11

## [0.0.2] - 2016-10-24
### Added
- Store a summary of the device records on disk #2, #4
- Monitor only mode (Produces no .csv for graphing) #8
- Will now place all log files in the given working directory

### Removed
- Remove graphs from README.md #13
- Remove numpy dependency (was not working on Termux)

## 0.0.1 - 2016-10-23
- Initial release

[Unreleased]: https://github.com/egeldenhuys/dalla-stats/compare/v0.2.3...HEAD
[0.2.3]: https://github.com/egeldenhuys/dalla-stats/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/egeldenhuys/dalla-stats/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/egeldenhuys/dalla-stats/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/egeldenhuys/dalla-stats/compare/v0.1.2...v0.2.0
[0.1.2+dev.1]: https://github.com/egeldenhuys/dalla-stats/compare/v0.1.1...v0.1.2+dev.1
[0.1.2]: https://github.com/egeldenhuys/dalla-stats/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/egeldenhuys/dalla-stats/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/egeldenhuys/dalla-stats/compare/v0.0.5...v0.1.0
[0.0.5]: https://github.com/egeldenhuys/dalla-stats/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/egeldenhuys/dalla-stats/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/egeldenhuys/dalla-stats/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/egeldenhuys/dalla-stats/compare/v0.0.1...v0.0.2
