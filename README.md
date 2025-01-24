# speechmatics-flow

Python client library and CLI for Speechmatics' Flow Service API.

## Getting started

To install from PyPI:

```bash
pip install speechmatics-flow
```

To install from source:

```bash
git clone https://github.com/speechmatics/speechmatics-flow
cd speechmatics-flow && python setup.py install
```

Windows users may need to run the install command with an extra flag:

```bash
python setup.py install --user
```

Instructions on how to create an account and generate an API
key can be found here: https://docs.speechmatics.com/flow/getting-started#set-up

## Example command-line usage

- Setting URLs for connecting to flow service. These values can be used in places of the --url flag:

*Note: Requires access to microphone

 ```bash
 speechmatics-flow --auth-token $TOKEN
 ```

### Change Assistant (Amelia → Humphrey)

To set the assistant to *Humphrey* instead of *Amelia* run this command:

```bash
speechmatics-flow --auth-token $TOKEN --assistant humphrey
```

### Load conversation_config from a config file

Instead of manually setting up conversation parameters, you can load them from a configuration file.

Create a JSON file with the template details, for example "conversation_config.json" and run flow client
using the `--config-file` option

```json
{
  "template_id": "flow-service-assistant-humphrey",
  "template_variables": {
    "persona": "You are an English butler named Humphrey.",
    "style": "Be charming but unpredictable.",
    "context": "You are taking a customer's order at a fast food restaurant."
  }
}
```

 ```bash
 speechmatics-flow --auth-token $TOKEN --config-file conversation_config.json
 ```

> **Hint**: Why limit Humphrey? Try changing the template_variables to see what happens if he’s not a butler but
> perhaps... a pirate, a celebrity chef, or a royal advisor. We won’t stop you. 🏴‍☠️

## Support

If you have any issues with this library or encounter any bugs then please get in touch with us at
support@speechmatics.com.
