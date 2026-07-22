# speechmatics-flow

> [!IMPORTANT]
> **This repository is legacy and is no longer maintained.**
>
> `speechmatics-flow` was the original Python client and CLI for the Speechmatics Flow API. It has been superseded and will not receive new features, fixes, or dependency updates. The repository remains online for reference only. Issues and pull requests are no longer monitored.

## Building a voice agent with Speechmatics today?

Don't start here. Start with the [Speechmatics SDKs](https://docs.speechmatics.com/integrations-and-sdks/sdks):

- **Integrations**: [LiveKit](https://docs.speechmatics.com/integrations-and-sdks/livekit/), [Pipecat](https://docs.speechmatics.com/integrations-and-sdks/pipecat/), or [Vapi](https://docs.speechmatics.com/integrations-and-sdks/vapi). The fastest path to a production voice agent.
- **Voice SDK**: [`speechmatics-voice`](https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/voice) for custom pipelines, with built-in turn detection, segmentation, and diarization.

Working examples live in the [Speechmatics Academy](https://github.com/speechmatics/speechmatics-academy).

## Already running Flow?

Flow bundled speech recognition, LLM orchestration, and text-to-speech behind a single WebSocket. The current Speechmatics stack is modular: the [Voice SDK](https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/voice) handles the listening side (turn detection, segmentation, speaker diarization) and you pair it with the LLM and [TTS](https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/tts) of your choice. The integrations above handle that orchestration for you.

Key differences at a glance:

| | Legacy Flow client (this repo) | Voice SDK |
|---|---|---|
| PyPI package | `speechmatics-flow` | `speechmatics-voice` |
| Import path | `speechmatics_flow` | `speechmatics.voice` |
| Client class | `WebsocketClient` | `VoiceAgentClient` |
| Scope | STT, LLM, and TTS via the Flow API | STT layer for agents; bring your own LLM and TTS |
| Source | this repository | [`speechmatics-python-sdk/sdk/voice`](https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/voice) |

> [!NOTE]
> If you need the legacy client while you plan your migration, pin it explicitly: `pip install speechmatics-flow==0.1.2`. Newer versions of the `speechmatics-flow` package name on PyPI are not this client.

---

<details>
<summary><strong>Legacy documentation</strong> (reference only, no longer updated)</summary>

## Getting started

To install from PyPI:

```bash
pip install speechmatics-flow==0.1.2
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

</details>

## Support

If you have questions about migrating away from this client, get in touch at
support@speechmatics.com or join the [Speechmatics Discord](https://discord.gg/wHQaMFzQJX).
