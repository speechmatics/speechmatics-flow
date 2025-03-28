from pytest import mark, param

from speechmatics_flow import cli
from speechmatics_flow.templates import Template

TEMPLATE_VARS = {
    "persona": "You are an English butler named Humphrey.",
    "style": "Be charming but unpredictable.",
    "context": "You are taking a customer's order at a fast food restaurant.",
}


@mark.parametrize(
    "args, exp_values",
    [
        param(
            [],
            {"template_id": Template.default.value},
            id="default assistant",
        ),
        param(
            ["--assistant=amelia"],
            {"template_id": Template.amelia.value},
            id="assistant amelia",
        ),
        param(
            ["--assistant=AMELIA"],
            {"template_id": Template.amelia.value},
            id="assistant AMELIA",
        ),
        param(
            ["--assistant=humphrey"],
            {"template_id": Template.humphrey.value},
            id="assistant humphrey",
        ),
        param(
            ["--assistant=demo-assistant"],
            {"template_id": "demo-assistant"},
            id="assistant demo",
        ),
        param(
            ["--config-file=tests/data/conversation_config.json"],
            {
                "template_id": "flow-service-assistant-humphrey",
                "template_variables": TEMPLATE_VARS,
            },
            id="params from config file",
        ),
        param(
            ["--assistant=amelia", "--config-file=tests/data/conversation_config.json"],
            {
                "template_id": "flow-service-assistant-amelia",
                "template_variables": TEMPLATE_VARS,
            },
            id="params from config file with assistant override from cli",
        ),
    ],
)
def test_get_conversation_config(args, exp_values):
    test_values = vars(cli.parse_args(args=args))
    config = cli.get_conversation_config(test_values)
    assert config.asdict() == exp_values, "Expecting {} but got {}".format(
        exp_values, config.asdict()
    )


@mark.parametrize(
    "args, exp_values",
    [
        param([], {"llm": False}),
        param(["--llm-debug-enabled"], {"llm": True}),
    ],
)
def test_get_debug_mode_settings(args, exp_values):
    test_args = vars(cli.parse_args(args=args))
    config = cli.get_debug_mode_settings(test_args)
    assert (
        config.asdict() == exp_values
    ), f"Expecting {exp_values}, got {config.asdict()}"
