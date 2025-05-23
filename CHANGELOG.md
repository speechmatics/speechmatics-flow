# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.3] - 2025-05-08

- Support for Application Inputs feature

## [0.1.2] - 2025-03-28

### Changed

- Removed `choices` from `--assistant` cli argument to support arbitrary strings
- Implemented case-insensitive lookup for predefined template names

## [0.1.1] - 2025-03-26

### Changed

- Include the package version when requesting a JWT

## [0.1.0] - 2025-02-13

### Added

- Added Debug mode
  - Introduced a new debug field in `StartConversation`.
  - When LLM debug mode is enabled, the client will receive debug messages with LLM request and response content

## [0.0.9] - 2025-01-24

### Fixed

- Issue with Flow latency on Linux

### Changed

- Examples load env vars from .env file
- Examples now print user/agent transcripts

## [0.0.8] - 2024-11-29

### Added

- Introduced a new class to enable custom configuration of audio playback settings, offering greater flexibility for
  fine-tuning audio playback.
- The client now buffers audio to ensure smoother playback, especially in challenging network conditions.

### Fixed

- Resolved an issue with reading piped audio from stdin.

## [0.0.7] - 2024-11-25

### Added

- Client-side function calling example
- Improved audio playback in examples
- Added instructions on how to generate an API KEY and how to install pyaudio

### Changed

- Set default URL when running from CLI

## [0.0.6] - 2024-11-18

### Added

- `tools` parameter: Introduced in the `client.run()` function to enable custom tool functionality.
- `ToolFunctionParam` class: Added for enhanced type-checking when building client functions.
- New message types: `ToolInvoke` and `ToolResult` messages are now supported for handling function calling.

### Changed

- StartConversation message: Updated to include the `tools` parameter.

## [0.0.5] - 2024-11-13

### Added

- Added the option to change the assistant from CLI
- Added the option to load conversation_config from a config file
- Added client handling of unexpected messages from the server

### Changed

- Allow versions of websockets from `10.0` up to and including `13.1` to mitigate extra_headers compatibility issue
  with websockets `14.0`
- Improved documentation for Interaction class

## [0.0.4] - 2024-11-12

### Added

- `ResponseStarted`: Indicates the start of TTS audio streaming from the server.
  The message contains the textual content of the utterance to be spoken.
- `ResponseInterrupted`: Indicates an interruption in the TTS audio stream from the server.
  The message contains the textual content up to the point where the utterance was stopped.
- `ResponseCompleted`: Indicates the completion of TTS audio transmission from the server.
  The message includes the textual content of the utterance just spoken.
- `ConversationEnding`: Indicates the session will continue in one-sided mode during TTS playback of the final words.
- `AddAudio`: Implicit name for all inbound binary messages.
  The client confirms receipt by sending an `ServerMessageType.AudioReceived` message.
- `AudioReceived`: Response to `ServerMessageType.AddAudio`, indicating that audio has been added successfully.
- Deprecation warning for `audio` (replaced by AddAudio) and `prompt` (replaced by Response*) messages

### Removed

- Unused `EndOfTranscript` server message

## [0.0.3] - 2024-10-23

### Changed

- PyAudio class is instantiated only when the client is started directly from the CLI.
- Simplified microphone example

### Fixed

- Choppy audio playback on some systems using Python 3.12+
- Latency issues on some systems using Python 3.12+

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
