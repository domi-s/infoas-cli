# InfoAs CLI

Read InfoAs problems, submit solutions and follow the judge from the terminal.

```
● Submission #48213 · suma-a-b
  ⎿ Judging… ⠹

     #  Verdict                     Points       Time
     1  ✓ Accepted                 10 / 10    0.004 s
     2  ✗ Wrong answer              0 / 10    0.003 s
     3  ⠹ pending                    - / -          -

  Score 10 / 100 · 1 / 3 tests passed · compiled in 0.41 s
```

## Install

Requires Python 3.9 or newer.

```bash
pipx install git+https://github.com/domi-s/infoas-cli
```

Or, from a clone: `pip install -e .`

## Access

The CLI uses API tokens, which are given on request at [infoas.ro/contact](https://infoas.ro/contact).
Tokens rotate daily.

## Commands

| Command | |
|---|---|
| `infoas login [username] [--token T]` | Log in and show your profile. Asks for whatever is missing. |
| `infoas logout` | Forget the saved token. |
| `infoas problem show <problem>` | Limits, input/output and the statement. |
| `infoas submit <problem> <file> [--wait]` | Submit a C++ or Python solution. Prints the submission ID, or with `--wait` follows it until it is judged. |
| `infoas submissions [--page N]` | Your submissions, newest first. |
| `infoas submission <id> [--wait]` | One submission: verdict, points and time per test, and the public tests. |

`<problem>` is the ID from the problem's link: `suma-a-b` for `infoas.ro/problema/suma-a-b`.

The statement is shown only to InfoAs staff. Everyone else gets the link to the problem.

The judge picks the language by itself: source containing `int main` or `#include` is C++11, anything else is
Python 3.12. The CLI warns you if this doesn't match the file's extension.

Every command takes `--json`, see [docs/json.md](docs/json.md).

### Exit codes

| Code | |
|---|---|
| 0 | Success, or a judged submission with 100 points |
| 1 | Judged with less than 100 points |
| 2 | Wrong command or arguments |
| 3 | Compilation error |
| 4 | Not logged in, or invalid token |
| 5 | Any other error (connection, rate limit, not found, ...) |

## Without a terminal

When the output is not a terminal (a pipe, a script, an AI agent such as Claude Code), there are no colours or
animations. `--wait` waits quietly and prints the final result once. `NO_COLOR` turns colours off in a terminal too.

## Configuration

Edit `infoas_cli/strings.py` and set `LANGUAGE = 'ro'` for Romanian.

The CLI talks to `https://infoas.ro`. The `INFOAS_URL` environment variable points it somewhere else, e.g. a local
Catalyst. Credentials are saved in `~/.config/infoas/credentials.json`, readable only by you.

## For InfoAs

Catalyst checks `X-InfoAs-User` and `Authorization: Bearer <token>`, where the token is

```
hmac_sha256(INFOAS_CLI_SECRET, "<date>|<username>")
```

`<date>` is today in Bucharest (`2026-11-03`). Yesterday's token keeps working until midnight UTC. Only the usernames
in `config/services.php` (`infoas_cli.users`) are allowed. To generate one:

```bash
python3 -c "import hmac,hashlib,datetime,zoneinfo,os;d=datetime.datetime.now(zoneinfo.ZoneInfo('Europe/Bucharest')).date().isoformat();print(hmac.new(os.environ['INFOAS_CLI_SECRET'].encode(),f'{d}|claude'.encode(),hashlib.sha256).hexdigest())"
```

Changing `INFOAS_CLI_SECRET` on the server cancels every token.

## Development

```bash
pip install -e . pytest
python3 -m pytest
```
