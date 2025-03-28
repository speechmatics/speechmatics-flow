"""Pre-configured Template IDs to start a Flow conversation."""

from enum import Enum
from typing import Literal


class Template(Enum):
    default = "default"
    amelia = "flow-service-assistant-amelia"
    humphrey = "flow-service-assistant-humphrey"


TemplateID = Literal[
    Template.default.value,
    Template.amelia.value,
    Template.humphrey.value,
]

# Map user-friendly name to full TemplateID
TEMPLATE_NAME_TO_ID = {member.name.lower(): member.value for member in Template}
