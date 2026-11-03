import os

VERSION = '1.0'

# InfoAs Catalyst. Override with the INFOAS_URL environment variable, e.g. for a local server.
INFOAS_URL = os.environ.get('INFOAS_URL', 'https://infoas.ro').rstrip('/')

CREDENTIALS_FILE = os.path.join(os.path.expanduser('~'), '.config', 'infoas', 'credentials.json')

# How long `--wait` follows a submission before giving up, in seconds
WAIT_TIMEOUT = 300
