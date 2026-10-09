#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Record and show manual capacity readings for one selected project.

Standalone source-only tool: no provider, model, network or auth request.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bridge.capacity import DEFAULT_MAX_AGE, CapacityError, CapacityStore  # noqa: E402


def _integer(text):
    try:
        return int(text, 10)
    except ValueError:
        raise argparse.ArgumentTypeError(f'not a whole number: {text!r}') from None


def _number(text):
    try:
        return float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f'not a number: {text!r}') from None


def _parser():
    parser = argparse.ArgumentParser(
        prog='capacity-readings.py',
        description='Manual capacity readings under PROJECT/coord/capacity/readings.json. '
                    'Never calls a provider; the source is always "manual".')
    parser.add_argument('--project', required=True, metavar='PATH', help='selected project directory')
    commands = parser.add_subparsers(dest='command', required=True)
    record = commands.add_parser('record', help='record one manual reading for one window')
    record.add_argument('--group', required=True, help='opaque shared-budget label')
    record.add_argument('--window', required=True, help='opaque window label, e.g. five-hour')
    record.add_argument('--window-minutes', required=True, type=_integer, help='window length in minutes')
    record.add_argument('--remaining-percent', required=True, type=_number, help='0 through 100')
    record.add_argument('--observed-at', required=True, help='timezone-aware ISO 8601 time')
    record.add_argument('--reset-at', help='optional timezone-aware ISO 8601 reset time')
    show = commands.add_parser('show', help='show readings and their freshness')
    show.add_argument('--group', help='only this shared-budget label (Unknown when absent)')
    show.add_argument('--json', action='store_true', help='print normalized JSON')
    show.add_argument('--max-age-seconds', type=_integer, default=DEFAULT_MAX_AGE,
                      help=f'fresh/stale boundary (default {DEFAULT_MAX_AGE})')
    return parser


def _percent(value):
    return 'none' if value is None else f'{value:g}%'


def _text(view):
    lines = [f'Readings: {view["state"]} (checked {view["checked_at"]}, '
             f'fresh within {view["max_age_seconds"]}s)']
    if view['error']:
        lines.append(f'  State refused: {view["error"]}')
    if not view['groups']:
        lines.append('  No groups recorded; capacity is Unknown.')
    for group, entry in view['groups'].items():
        lines.append(f'Group {group}:')
        if entry['status'] == 'unknown':
            lines.append('  Unknown: no valid reading.')
        for window, reading in entry['windows'].items():
            lines += [f'  Window {window} ({reading["window_minutes"]} min): {reading["status"]}',
                      f'    Source: {reading["source"]}',
                      f'    Observed: {reading["observed_at"]} (age {reading["age_seconds"]:.0f}s)',
                      f'    Reset: {reading["reset_at"] or "not recorded"}',
                      f'    Last reading: {_percent(reading["last_reading_remaining_percent"])} remaining',
                      f'    Usable now: {_percent(reading["usable_remaining_percent"])}']
    return '\n'.join(lines)


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        store = CapacityStore(args.project)
        if args.command == 'record':
            reading = store.record(args.group, args.window, args.window_minutes, args.remaining_percent,
                                   args.observed_at, args.reset_at)
            print(f'Recorded manual reading {args.group}/{args.window} observed {reading["observed_at"]}.')
            return 0
        view = store.show(args.group, args.max_age_seconds)
    except (CapacityError, OSError) as error:
        print(f'capacity-readings: refused: {error}', file=sys.stderr)
        return 1
    print(json.dumps(view, indent=2) if args.json else _text(view))
    return 1 if view['state'] == 'invalid' else 0


if __name__ == '__main__':
    sys.exit(main())
