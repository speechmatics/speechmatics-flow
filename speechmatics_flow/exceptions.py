# (c) 2024, Cantab Research Ltd.
"""
Exceptions and errors used by the library.
"""


class ConversationError(Exception):
    """
    Indicates an error in flow conversation session.
    """


class ForceEndSession(Exception):
    """
    Can be raised by the user from a middleware or event handler
     to force the transcription session to end early.
    """


class ConversationEndedException(Exception):
    """
    Indicates the conversation session ended.
    """
