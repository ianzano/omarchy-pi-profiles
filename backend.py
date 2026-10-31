#!/usr/bin/env python3
"""Small JSON bridge to the installed pi-profiles CLI; never reads credentials."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def executable(name):
    found = shutil.which(name)
    if found:
        return found
    shim = Path.home() / '.local/share/mise/shims' / name
    if shim.is_file():
        return str(shim)
    raise ValueError(f'{name} is not available. Install it and ensure it is on the desktop PATH.')


def run_ppi(*args):
    result = subprocess.run([executable('ppi'), *args], text=True, capture_output=True, timeout=15)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or 'ppi failed')
    return result.stdout


def inventory():
    profiles = []
    for line in run_ppi('list').splitlines():
        if '\t' not in line:
            continue
        label, path = line.split('\t', 1)
        default = label.startswith('* ')
        name = label[2:]
        if re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}', name):
            profiles.append({'name': name, 'path': path, 'isDefault': default})
    return profiles


def execute(action, name=''):
    if action == 'list':
        return {'ok': True, 'profiles': inventory()}
    if action not in ('launch', 'set-default', 'remove'):
        raise ValueError('Unknown action')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}', name):
        raise ValueError('Invalid profile name')
    if name not in [p['name'] for p in inventory()]:
        raise ValueError('That profile no longer exists. Refresh the list.')
    if action == 'launch':
        # Omarchy chooses the terminal and the active terminal's working directory.
        # A terminal can outlive its launcher and inherit its pipes. Never wait
        # for that terminal or let it retain the JSON bridge's descriptors.
        process = subprocess.Popen(
            [executable('omarchy'), 'launch', 'terminal', executable('ppi'), 'use', name],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            code = process.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            code = None  # The independent launcher is still starting the terminal.
        if code not in (None, 0):
            raise ValueError(f'Could not launch the terminal (exit {code})')
        return {'ok': True, 'message': f'Launched {name}'}
    run_ppi(*(['set-default', name] if action == 'set-default' else ['delete', name, '--force']))
    return {'ok': True, 'profiles': inventory(),
            'message': f'Default set to {name}' if action == 'set-default' else f'Removed {name}'}


def main():
    try:
        result = execute(*sys.argv[1:])
    except (ValueError, OSError, subprocess.SubprocessError, TypeError) as error:
        result = {'ok': False, 'message': str(error)}
    print(json.dumps(result))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
