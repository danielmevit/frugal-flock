#!/usr/bin/env python3
import argparse
import sys
import json
from bridge.capacity import CapacityStore

def main():
    parser = argparse.ArgumentParser(description="Manage capacity readings")
    parser.add_argument("--project", required=True, help="Project directory path")

    subparsers = parser.add_subparsers(dest="command", required=True)

    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--group", required=True)
    record_parser.add_argument("--window", required=True)
    record_parser.add_argument("--window-minutes", type=int, required=True)
    record_parser.add_argument("--remaining-percent", type=float, required=True)
    record_parser.add_argument("--observed-at", required=True)
    record_parser.add_argument("--reset-at", required=False)

    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("--group", required=False)
    show_parser.add_argument("--json", action="store_true", help="Output as JSON")
    show_parser.add_argument("--max-age-seconds", type=int, default=900)

    args = parser.parse_args()

    try:
        store = CapacityStore(args.project)

        if args.command == "record":
            store.record(
                group=args.group,
                window=args.window,
                window_minutes=args.window_minutes,
                remaining_percent=args.remaining_percent,
                observed_at=args.observed_at,
                reset_at=args.reset_at
            )
            print("Recorded successfully.")

        elif args.command == "show":
            result = store.show(group=args.group, max_age_seconds=args.max_age_seconds)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                for group, windows in result.items():
                    print(f"Group: {group}")
                    if "status" in windows and windows["status"] == "Unknown":
                        print("  Unknown")
                        continue

                    for window, data in windows.items():
                        print(f"  Window: {window} ({data.get('window_minutes')}m)")
                        print(f"    Status: {data.get('status')}")
                        print(f"    Source: {data.get('source')}")
                        print(f"    Observed at: {data.get('observed_at')} (age: {data.get('age_seconds'):.1f}s)")
                        if "reset_at" in data:
                            print(f"    Reset at: {data.get('reset_at')}")

                        if "usable_remaining_percent" in data:
                            print(f"    Usable remaining: {data['usable_remaining_percent']}%")
                        if "last_remaining_percent" in data:
                            print(f"    Last remaining: {data['last_remaining_percent']}% (not usable)")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
