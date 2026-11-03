# JSON output

With `--json`, every command prints one JSON object per line, and nothing else. Text is UTF-8 (`ensure_ascii` is off).
The exit codes are the same as without `--json`.

## Errors

```json
{"error": "unauthorized"}
```

| Error | |
|---|---|
| `not_logged_in` | No saved token |
| `unauthorized` | Invalid username or token |
| `forbidden` | The submission is not yours |
| `not_found`, `problem_not_found` | |
| `problem_not_public` | Submitting to a problem that isn't public |
| `no_code_provided` | Empty file |
| `submission_limit_exceeded_user` | Your submission limit (5 per minute, 60 per hour, 360 per day) |
| `submission_limit_exceeded_all` | InfoAs' limit for everyone (90 per minute) |
| `too_many_requests` | More than 120 API requests in a minute |
| `connection` | InfoAs could not be reached |
| `server` | Any other HTTP error |

## `login`

```json
{"name": "Claude Code", "username": "claude", "url": "https://infoas.ro/@claude"}
```

## `logout`

```json
{"success": "logged_out"}
```

## `problem show`

```json
{
  "content_id": "suma-a-b",
  "name": "Suma",
  "difficulty": "EASY",
  "time_limit": 1,
  "total_limit": 64,
  "stack_limit": 8,
  "io_method": "CONSOLE",
  "tags": ["math"],
  "url": "https://infoas.ro/problema/suma-a-b",
  "task": "Markdown",
  "examples": [{"input": "1 2\n", "output": "3\n", "explanation": "Markdown"}],
  "io_description": {"input": "suma.in", "output": "suma.out"}
}
```

`io_method` is `CONSOLE`, `FILES` or `FUNCTION`. `task`, `examples` and `io_description` are only there for InfoAs
staff. Time is in seconds and memory in MB.

## `submit`

Without `--wait`:

```json
{"id": 48213, "uuid": "4ad003de-3037-4ef5-bddc-71b772033055"}
```

With `--wait`, the same lines as `submission --wait`.

## `submission`

```json
{
  "id": 48213,
  "problem": {"content_id": "suma-a-b", "name": "Suma"},
  "status": "done",
  "result": "finished",
  "score": 25,
  "details": {
    "compilation_output": "",
    "compilation_time": 0.41,
    "execution_time": 0.06,
    "points": 25,
    "test_count": 2,
    "tests": [
      {"index": 1, "message": "Răspuns corect!", "points": "10", "max_points": 10, "execution_time": 0.004},
      {"index": 2, "message": "Răspuns greșit.", "points": "0", "max_points": 10, "execution_time": 0.012,
       "input": "2 2\n", "expected_output": "4\n", "user_output": "5\n"}
    ]
  },
  "created_at": "2026-11-03T12:43:47.000000Z"
}
```

- `status`: `pending` (waiting for the judge), `judging` or `done`.
- `result`: `pending`, `finished`, `compilation_error` or `rogue` (the judge could not evaluate it).
- `details` comes from the judge as it is. While judging, `tests` holds the tests judged so far and `test_count` the
  total. `points` in a test can be a string. The messages are in Romanian.
- Only public tests have `input`, `expected_output` and `user_output`.

With `--wait`, a new line is printed every time the submission changes. The last one has `"status": "done"`.

## `submissions`

```json
{
  "page": 1,
  "last_page": 3,
  "submissions": [
    {"id": 48213, "problem": {"content_id": "suma-a-b", "name": "Suma"}, "status": "done", "result": "finished",
     "score": 25, "created_at": "2026-11-03T12:43:47.000000Z"}
  ]
}
```

25 per page, newest first.
