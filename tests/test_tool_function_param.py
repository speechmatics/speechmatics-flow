from pytest import mark, param

from speechmatics_flow.tool_function_param import ToolFunctionParam


@mark.parametrize(
    "params",
    [
        param(
            {
                "type": "function",
                "function": {
                    "name": "test_function",
                    "description": "test_description",
                },
            },
            id="function without optional params",
        ),
        param(
            {
                "type": "function",
                "function": {
                    "name": "test_function",
                    "description": "test_description",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {
                                "type": "int",
                                "description": "First number",
                            },
                            "b": {
                                "type": "int",
                                "description": "Second number",
                            },
                        },
                        "required": ["a", "b"],
                    },
                },
            },
            id="function with optional params",
        ),
    ],
)
def test_websocket_function(params):
    websocket_function = ToolFunctionParam(**params)
    assert dict(websocket_function) == params
