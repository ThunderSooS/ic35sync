"""Conservative task deletion comparison; only root VTODO timestamp values vary."""
from datetime import datetime
import re


def masked_task(content):
    if not isinstance(content, str):
        raise ValueError('Calendar content missing')
    stack, output = [], []
    counts = {'DTSTAMP': 0, 'LAST-MODIFIED': 0}
    calendars = todos = 0
    previous_stamp = False
    for line in content.splitlines(keepends=True):
        body = line.rstrip('\r\n')
        ending = line[len(body):]
        if body.startswith((' ', '\t')) and previous_stamp:
            raise ValueError('Folded timestamp unsupported')
        previous_stamp = False
        if body.startswith('BEGIN:'):
            name = body[6:]
            if not stack:
                if name != 'VCALENDAR':
                    raise ValueError('Unexpected root')
                calendars += 1
            stack.append(name)
            if stack == ['VCALENDAR', 'VTODO']:
                todos += 1
        elif body.startswith('END:'):
            if not stack or stack.pop() != body[4:]:
                raise ValueError('Unbalanced calendar')
        elif stack == ['VCALENDAR', 'VTODO']:
            name, separator, value = body.partition(':')
            if name in counts and separator:
                if not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z', value):
                    raise ValueError('Invalid timestamp')
                datetime.strptime(value, '%Y%m%dT%H%M%SZ')
                counts[name] += 1
                previous_stamp = True
                line = name + ':<timestamp>' + ending
        output.append(line)
    if stack or calendars != 1 or todos != 1 or counts['DTSTAMP'] != 1 or counts['LAST-MODIFIED'] > 1:
        raise ValueError('Unsupported calendar structure')
    return ''.join(output)


def remote_unchanged_for_delete(remote, binding):
    if remote.get('error') or remote.get('uid') != binding.get('uid'):
        return False
    if remote['semantic'] != binding['remote']:
        return False
    current = remote.get('content')
    previous = binding.get('remote_content', current)
    if previous == current:
        return True
    if remote.get('kind') != 'tasks':
        return False
    try:
        return masked_task(previous) == masked_task(current)
    except (ValueError, TypeError):
        return False
