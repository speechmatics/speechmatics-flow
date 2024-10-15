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

## Example command-line usage

- Setting URLs for connecting to flow service. These values can be used in places of the --url flag:

*Note: Requires access to microphone

 ```bash
 speechmatics-flow --url $URL --auth-token $TOKEN -
 ```

## Support

If you have any issues with this library or encounter any bugs then please get in touch with us at
support@speechmatics.com.
