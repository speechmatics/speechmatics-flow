# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.0.2] - 2024-10-17

### Added

- Improved handling of the AudioEnded which caused the client to abruptly close the connection.
  The client now waits up to 5 seconds for a ConversationEnded message from the server before closing the connection.

### Changed

- Do not generate JWT when connecting to a local Flow server.
- `TranscriptionError` is now `ConversationError`

### Fixed

- CLI usage example from README using `-` which caused an `unrecognized arguments` error.
- Stream from microphone example using ssl_context=None

### Removed

- `EndOfTranscriptException` from exceptions

## [0.0.1] - 2024-10-14

### Added

- Add speechmatics-flow client
