import argparse
import getpass
import json
import sys
import time

from infoas_cli import api, display
from infoas_cli.config import INFOAS_URL, VERSION, WAIT_TIMEOUT
from infoas_cli.strings import t

# Exit codes
EXIT_OK = 0
EXIT_NOT_FULL_SCORE = 1
EXIT_COMPILATION_ERROR = 3
EXIT_AUTH = 4
EXIT_ERROR = 5


def output_json(data):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def submission_exit_code(data):
    if data['status'] != 'done':
        return EXIT_OK
    if data['result'] == 'compilation_error':
        return EXIT_COMPILATION_ERROR
    if float(data.get('score') or 0) < 100:
        return EXIT_NOT_FULL_SCORE
    return EXIT_OK


def detect_language(code):
    # Same rule as the judge
    return 'C++' if 'int main' in code or '#include' in code else 'Python'


def login(args):
    username = args.username or input(t('username')).strip()
    token = args.token or getpass.getpass(t('token')).strip()
    credentials = {'username': username, 'token': token}

    user = api.me(credentials)
    api.save_credentials(username, token)

    user['url'] = f"{INFOAS_URL}/@{user['username']}"

    if args.json:
        output_json(user)
    else:
        print(display.green('✓ ' + t('logged_in')))
        display.profile(user)

    return EXIT_OK


def logout(args):
    api.delete_credentials()

    if args.json:
        output_json({'success': 'logged_out'})
    else:
        print(t('logged_out'))

    return EXIT_OK


def problem_show(args):
    data = api.get_problem(args.problem)

    if args.json:
        output_json(data)
    else:
        display.problem(data)

    return EXIT_OK


def submit(args):
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            code = f.read()
    except OSError:
        display.error(t('error_file', file=args.file))
        return EXIT_ERROR

    language = detect_language(code)
    extension = args.file.rsplit('.', 1)[-1].lower()
    if not args.json and ((extension == 'py' and language == 'C++') or (extension in ('cpp', 'cc', 'cxx') and language == 'Python')):
        print(display.yellow(t('language_warning', language=language)), file=sys.stderr)

    submission = api.submit(args.problem, code)

    if not args.wait:
        if args.json:
            output_json(submission)
        else:
            print(t('submitted', id=submission['id']))
        return EXIT_OK

    return follow(submission['id'], args.json)


def follow(submission_id, as_json):
    """Polls a submission every second until it is judged."""

    live = sys.stdout.isatty() and not as_json
    started = time.time()
    last = None
    drawn = 0
    frame = 0

    while True:
        data = api.get_submission(submission_id)

        if as_json:
            # One line per change, the last one has status `done`
            if data != last:
                output_json(data)
        elif live:
            # Animate the spinner for a second, then ask the server again
            for _ in range(10):
                lines = display.submission(data, frame)
                if drawn:
                    sys.stdout.write(f'\033[{drawn}F\033[J')
                sys.stdout.write('\n'.join(lines) + '\n')
                sys.stdout.flush()
                drawn = len(lines)
                frame += 1

                if data['status'] == 'done':
                    break
                time.sleep(0.1)

        last = data

        if data['status'] == 'done':
            break

        if time.time() - started > WAIT_TIMEOUT:
            if not as_json:
                print(display.yellow(t('still_judging', id=submission_id)))
            return EXIT_ERROR

        if not live:
            time.sleep(1)

    # Without a terminal (e.g. inside Claude Code) only the final result is printed
    if not live and not as_json:
        print('\n'.join(display.submission(data)))

    return submission_exit_code(data)


def submission(args):
    if args.wait:
        return follow(args.id, args.json)

    data = api.get_submission(args.id)

    if args.json:
        output_json(data)
    else:
        print('\n'.join(display.submission(data)))

    return submission_exit_code(data)


def submissions(args):
    data = api.get_submissions(args.page)

    if args.json:
        output_json(data)
    else:
        display.submissions(data)

    return EXIT_OK


def build_parser():
    parser = argparse.ArgumentParser(
        prog='infoas',
        description='Solve InfoAs problems from the terminal.',
        epilog=f'API tokens are given on request: {INFOAS_URL}/contact',
    )
    parser.add_argument('--version', action='version', version=f'infoas-cli {VERSION}')

    # Shared by every command, so `--json` works anywhere on the line
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--json', action='store_true', help='print JSON instead of text')

    commands = parser.add_subparsers(dest='command', required=True, metavar='command')

    command = commands.add_parser('login', parents=[common], help='log in with your username and API token',
                                  epilog=f'API tokens are given on request: {INFOAS_URL}/contact')
    command.add_argument('username', nargs='?')
    command.add_argument('--token', help='the API token (asked for if missing)')
    command.set_defaults(handler=login)

    command = commands.add_parser('logout', parents=[common], help='forget the saved token')
    command.set_defaults(handler=logout)

    command = commands.add_parser('problem', help='problem commands')
    problem_commands = command.add_subparsers(dest='problem_command', required=True, metavar='command')
    command = problem_commands.add_parser('show', parents=[common], help='show a problem')
    command.add_argument('problem', help='the problem ID from its link, e.g. suma-a-b')
    command.set_defaults(handler=problem_show)

    command = commands.add_parser('submit', parents=[common], help='submit a solution (C++ or Python)')
    command.add_argument('problem', help='the problem ID from its link, e.g. suma-a-b')
    command.add_argument('file')
    command.add_argument('--wait', action='store_true', help='follow the submission until it is judged')
    command.set_defaults(handler=submit)

    command = commands.add_parser('submissions', parents=[common], help='list your submissions')
    command.add_argument('--page', type=int, default=1)
    command.set_defaults(handler=submissions)

    command = commands.add_parser('submission', parents=[common], help='show a submission')
    command.add_argument('id', type=int)
    command.add_argument('--wait', action='store_true', help='follow the submission until it is judged')
    command.set_defaults(handler=submission)

    return parser


def main(argv=None):
    # On Windows, output that isn't a console (a pipe, Claude Code) uses the locale encoding,
    # e.g. cp1252, which can't print Romanian letters
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8')

    args = build_parser().parse_args(argv)

    try:
        return args.handler(args)
    except api.ApiError as e:
        if args.json:
            output_json({'error': e.error})
        elif e.error == 'not_logged_in':
            display.error(t('not_logged_in'))
            print(t('token_help', url=INFOAS_URL), file=sys.stderr)
        elif e.error == 'unauthorized':
            display.error(t('error_unauthorized'))
            print(t('token_help', url=INFOAS_URL), file=sys.stderr)
        else:
            display.error(t('error_' + e.error, url=INFOAS_URL, status=e.status))

        return EXIT_AUTH if e.error in ('not_logged_in', 'unauthorized') else EXIT_ERROR
    except KeyboardInterrupt:
        return EXIT_ERROR


if __name__ == '__main__':
    sys.exit(main())
