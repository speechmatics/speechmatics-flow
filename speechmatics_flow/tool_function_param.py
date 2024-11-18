"""Define a set of typed dictionaries to represent a structured message
for a client side function, using TypedDict for type enforcement.

Example:
    tool_function = ToolFunctionParam(
        type="function",
        function={
            "name": "add_nums",
            "description": "Adds two numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "int", "description": "First number"},
                    "b": {"type": "int", "description": "Second number"}
                },
                "required": ["a", "b"]
            }
        }
    )

    # Convert to dictionary
    dict(tool_function)
"""

import sys

from typing import Literal, Optional, Dict, List, TypedDict

if sys.version_info < (3, 11):
    from typing_extensions import Required
else:
    from typing import Required


class Property(TypedDict):
    type: Required[str]
    description: Required[str]


class FunctionParam(TypedDict, total=False):
    type: Required[str]
    properties: Required[Dict[str, Property]]
    required: Optional[List[str]]


class FunctionDefinition(TypedDict, total=False):
    name: Required[str]
    """The name of the function to be called."""

    description: Optional[str]
    """The description of what the function does, used by the model to choose
    when and how to call the function.
    """

    parameters: Optional[FunctionParam]
    """The parameters of the function to be called."""


class ToolFunctionParam(TypedDict):
    type: Required[Literal["function"]]
    """Currently, only 'function' is supported."""

    function: Required[FunctionDefinition]
