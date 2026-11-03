import json
import os

import requests

from infoas_cli.config import INFOAS_URL, CREDENTIALS_FILE, VERSION


class ApiError(Exception):
    def __init__(self, error, status=None):
        super().__init__(error)
        self.error = error
        self.status = status


def load_credentials():
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save_credentials(username, token):
    os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)

    # Readable only by the current user
    fd = os.open(CREDENTIALS_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump({'username': username, 'token': token}, f)


def delete_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        os.remove(CREDENTIALS_FILE)


def request(method, path, credentials=None, **kwargs):
    if credentials is None:
        credentials = load_credentials()
    if credentials is None:
        raise ApiError('not_logged_in')

    headers = kwargs.pop('headers', {})
    headers['Accept'] = 'application/json'
    headers['User-Agent'] = f'infoas-cli/{VERSION}'
    headers['X-InfoAs-User'] = credentials['username']
    headers['Authorization'] = f"Bearer {credentials['token']}"

    try:
        response = requests.request(method, f'{INFOAS_URL}/api/cli{path}', headers=headers, timeout=20, **kwargs)
    except requests.RequestException:
        raise ApiError('connection')

    try:
        data = response.json()
    except ValueError:
        data = None

    # Errors can come with a 200 status too (e.g. the submission limits)
    if isinstance(data, dict) and 'error' in data:
        raise ApiError(data['error'], response.status_code)

    if response.status_code == 429:
        raise ApiError('too_many_requests', 429)
    if response.status_code == 404:
        raise ApiError('not_found', 404)
    if response.status_code != 200 or data is None:
        raise ApiError('server', response.status_code)

    return data


def me(credentials=None):
    return request('GET', '/me', credentials)


def get_problem(content_id):
    return request('GET', f'/problems/{content_id}')


def submit(content_id, code):
    # Catalyst reads the problem from the referer, like on the website
    headers = {'Referer': f'{INFOAS_URL}/problema/{content_id}'}
    return request('POST', '/submissions', json={'code': code}, headers=headers)['submission']


def get_submissions(page=1):
    return request('GET', '/submissions', params={'page': page})


def get_submission(submission_id):
    return request('GET', f'/submissions/{submission_id}')
