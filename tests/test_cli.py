import json

import pytest

from infoas_cli import api, display, main


class Response:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self.data = data

    def json(self):
        if self.data is None:
            raise ValueError()
        return self.data


@pytest.fixture
def logged_in(monkeypatch):
    monkeypatch.setattr(api, 'load_credentials', lambda: {'username': 'claude', 'token': 'abc'})


def fake_requests(monkeypatch, response):
    calls = []

    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return response

    monkeypatch.setattr(api.requests, 'request', request)
    return calls


def test_submit_sends_problem_in_referer(monkeypatch, logged_in):
    calls = fake_requests(monkeypatch, Response(200, {'submission': {'id': 7, 'uuid': 'x'}}))

    assert api.submit('suma-a-b', 'int main(){}') == {'id': 7, 'uuid': 'x'}

    method, url, kwargs = calls[0]
    assert method == 'POST' and url.endswith('/api/cli/submissions')
    assert kwargs['headers']['Referer'].endswith('/problema/suma-a-b')
    assert kwargs['headers']['X-InfoAs-User'] == 'claude'
    assert kwargs['headers']['Authorization'] == 'Bearer abc'


def test_error_with_200_status(monkeypatch, logged_in):
    fake_requests(monkeypatch, Response(200, {'error': 'submission_limit_exceeded_user'}))

    with pytest.raises(api.ApiError) as e:
        api.submit('suma-a-b', 'int main(){}')
    assert e.value.error == 'submission_limit_exceeded_user'


def test_not_logged_in(monkeypatch, capsys):
    monkeypatch.setattr(api, 'load_credentials', lambda: None)

    assert main.main(['submissions', '--json']) == main.EXIT_AUTH
    assert json.loads(capsys.readouterr().out) == {'error': 'not_logged_in'}


def test_avatar_is_mirrored_and_stable():
    picture = display.avatar('claude')

    assert picture == display.avatar('claude')
    assert len(picture) == 5
    for row in picture:
        assert row == ''.join(reversed([row[i:i + 2] for i in range(0, 10, 2)]))


def test_partial_submission_shows_pending_tests():
    data = {
        'id': 3,
        'status': 'judging',
        'result': 'pending',
        'details': {
            'test_count': 3,
            'tests': [{'index': 1, 'message': 'Răspuns corect!', 'points': '50', 'max_points': 50, 'execution_time': 0.01}],
        },
    }

    text = '\n'.join(display.submission(data))

    assert 'Accepted' in text
    assert text.count('pending') == 2
    assert '1 / 3 tests passed' in text


def test_exit_codes():
    assert main.submission_exit_code({'status': 'done', 'result': 'finished', 'score': 100}) == main.EXIT_OK
    assert main.submission_exit_code({'status': 'done', 'result': 'finished', 'score': 40}) == main.EXIT_NOT_FULL_SCORE
    assert main.submission_exit_code({'status': 'done', 'result': 'compilation_error', 'score': 0}) == main.EXIT_COMPILATION_ERROR
