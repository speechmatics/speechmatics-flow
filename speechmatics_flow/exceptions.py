# (c) 2024, Cantab Research Ltd.
"""
Exceptions and errors used by the library.
"""


class TranscriptionError(Exception):
    """
    Indicates an error in transcription.
    """


class EndOfTranscriptException(Exception):
    """
    Indicates that the transcription session has finished.
    """


class ForceEndSession(Exception):
    """
    Can be raised by the user from a middleware or event handler
     to force the transcription session to end early.
    """


class ConversationEndedException(Exception):
    """
    Indicates the session ended.
    """
