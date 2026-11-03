import hashlib
import os
import sys

from infoas_cli.strings import t

COLOR = sys.stdout.isatty() and 'NO_COLOR' not in os.environ

SPINNER = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'


def paint(text, *codes):
    if not COLOR or not codes:
        return str(text)
    return f"\033[{';'.join(str(code) for code in codes)}m{text}\033[0m"


def bold(text):
    return paint(text, 1)


def dim(text):
    return paint(text, 2)


def red(text):
    return paint(text, 31)


def green(text):
    return paint(text, 32)


def yellow(text):
    return paint(text, 33)


def blue(text):
    return paint(text, 34)


def error(message):
    print(red(f'✗ {message}'), file=sys.stderr)


def avatar(username):
    """5x5 mirrored block pattern made from the username, like a GitHub identicon."""

    digest = hashlib.md5(username.encode()).digest()
    color = 31 + digest[15] % 6

    lines = []
    for row in range(5):
        cells = [digest[row * 3 + col] % 2 == 0 for col in range(3)]
        cells = cells + cells[1::-1]
        lines.append(''.join(paint('██', color) if cell else '  ' for cell in cells))

    return lines


def profile(user):
    url = user['url']

    info = [
        bold(user['name']),
        dim('@' + user['username']),
        '',
        f"{t('profile'):<10} {blue(url)}",
        f"{t('logout'):<10} {blue('infoas logout')}",
    ]

    print()
    for picture, text in zip(avatar(user['username']), info):
        print(f'  {picture}   {text}')
    print()


def markdown(text):
    """Barely any formatting: headings in bold, everything else as it is."""

    for line in text.strip().splitlines():
        if line.startswith('#'):
            print(bold(line.lstrip('#').strip()))
        else:
            print(line)


def problem(data):
    io_method = data.get('io_method')
    io_description = data.get('io_description') or {}

    print(bold(data['name']) + '  ' + dim(data['url']))
    print()
    print(f"  {t('difficulty'):<11}{data.get('difficulty')}")
    print(f"  {t('time'):<11}{data.get('time_limit')} s")
    print(f"  {t('memory'):<11}{data.get('total_limit')} MB / {data.get('stack_limit')} MB")

    if io_method == 'FILES' and io_description:
        print(f"  {t('input'):<11}{io_description.get('input')}")
        print(f"  {t('output'):<11}{io_description.get('output')}")
    elif io_method:
        print(f"  {t('input'):<11}{t('console')}")

    if data.get('tags'):
        print(f"  {t('tags'):<11}{', '.join(str(tag) for tag in data['tags'])}")

    print()

    if 'task' not in data:
        print(t('statement_hidden') + ' ' + blue(data['url']))
        return

    markdown(data['task'] or '')

    for index, example in enumerate(data.get('examples') or [], start=1):
        print()
        print(bold(t('example', index=index)))
        print(dim(t('input')))
        print(example.get('input', '').rstrip())
        print(dim(t('output')))
        print(example.get('output', '').rstrip())

        if example.get('explanation'):
            print(dim(t('explanation')))
            print(example['explanation'].strip())


def verdict_color(points, max_points):
    if points >= max_points:
        return green
    if points > 0:
        return yellow
    return red


def to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def submission(data, frame=0):
    """Returns the lines for a submission, so the live view can redraw them."""

    details = data.get('details') or {}
    tests = details.get('tests') or []
    test_count = max(details.get('test_count') or 0, len(tests))
    done = data['status'] == 'done'
    spinner = SPINNER[frame % len(SPINNER)]

    title = t('submission', id=data['id'])
    if data.get('problem'):
        title += dim(f" · {data['problem']['content_id']}")

    lines = ['', paint('●', 34) + ' ' + bold(title)]

    if not done:
        state = t('judging') if data['status'] == 'judging' else t('queued')
        lines.append(dim('  ⎿ ') + f'{state}… ' + blue(spinner))

    if data.get('result') == 'compilation_error':
        lines.append(dim('  ⎿ ') + red(t('compilation_error')))
        lines.append('')
        for line in (details.get('compilation_output') or '').strip().splitlines()[:40]:
            lines.append('    ' + dim(line))
        return lines

    if data.get('result') == 'rogue':
        lines.append(dim('  ⎿ ') + red(t('rogue')))
        return lines

    if test_count == 0:
        return lines

    lines.append('')
    lines.append(dim(f"   {'#':>3}  {t('verdict'):<24}{t('points'):>10}  {t('time'):>9}"))

    for test in tests:
        points = to_number(test.get('points'))
        max_points = to_number(test.get('max_points'))
        color = verdict_color(points, max_points)
        mark = '✓' if points >= max_points else '✗'

        message = f"{mark} {t(test.get('message', '').strip())}"
        score = f"{points:g} / {max_points:g}"
        time = f"{to_number(test.get('execution_time')):.3f} s"

        lines.append(f"   {test.get('index'):>3}  {color(f'{message:<24}')}{score:>10}  {time:>9}")

    for index in range(len(tests) + 1, test_count + 1):
        pending = f"{spinner} {t('pending')}"
        lines.append(dim(f"   {index:>3}  {pending:<24}{'- / -':>10}  {'-':>9}"))

    passed = sum(1 for test in tests if to_number(test.get('points')) >= to_number(test.get('max_points')))
    points = sum(to_number(test.get('points')) for test in tests)

    summary = [
        verdict_color(points, 100)(t('score', points=f'{points:g}')),
        t('tests_passed', passed=passed, count=test_count),
    ]
    if details.get('compilation_time'):
        summary.append(t('compiled_in', time=details['compilation_time']))

    lines.append('')
    lines.append('  ' + dim(' · ').join(summary))

    for test in tests:
        if 'input' in test:
            lines.extend(public_test(test))

    return lines


def public_test(test):
    expected = (test.get('expected_output') or '').rstrip().splitlines()
    output = (test.get('user_output') or '').rstrip().splitlines()

    lines = ['', bold(f"  {t('public_test', index=test['index'])}")]

    def block(label, rows, compare=None):
        rows = rows[:20] or [dim(t('no_output'))]
        for i, row in enumerate(rows):
            # Lines that differ from the expected output are shown in red
            if compare is not None and (i >= len(compare) or row.strip() != compare[i].strip()):
                row = red(row)
            label_text = label if i == 0 else ''
            lines.append('    ' + dim(f'{label_text:<12}│ ') + row)

    block(t('input'), (test.get('input') or '').rstrip().splitlines())
    block(t('expected'), expected)
    block(t('your_output'), output, expected)

    return lines


def submissions(data):
    if not data['submissions']:
        print(t('no_submissions'))
        return

    print(dim(f"  {'ID':>8}  {t('problem'):<30}  {t('verdict'):<20}  {t('date')}"))

    for item in data['submissions']:
        problem_name = (item.get('problem') or {}).get('content_id', '-')

        if item['status'] != 'done':
            verdict = blue(f"{t('pending'):<20}")
        elif item['result'] == 'compilation_error':
            verdict = red(f"{t('compilation_error'):<20}")
        else:
            score = to_number(item['score'])
            verdict = verdict_color(score, 100)(f"{score:g} / 100".ljust(20))

        date = (item.get('created_at') or '')[:16].replace('T', ' ')
        print(f"  {item['id']:>8}  {problem_name[:30]:<30}  {verdict}  {dim(date)}")

    if data['last_page'] > 1:
        print()
        print(dim('  ' + t('page', page=data['page'], last_page=data['last_page'])))
