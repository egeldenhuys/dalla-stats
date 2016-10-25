# Changelog

This project adheres to [Semantic Versioning](http://semver.org/).

## Unreleased
### Added
- Log timestamp to console when fetching records

## 0.0.3 - 2016-10-24
### Added
- Port to Python 3

### Fixed
- Handles router errors #10
- Keeps data on restart #11

## 0.0.2 - 2016-10-24
### Added
- Store a summary of the device records on disk #4, #2,
- Monitor only mode (Produces no .csv for graphing) #8
- Will now place all log files in the given working directory

### Removed
- Remove numpy dependency (was not working on Termux)
- Remove graphs from README.md #13

## 0.0.1 - 2016-10-23
- Initial release
