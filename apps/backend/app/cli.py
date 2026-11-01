from __future__ import annotations

import argparse
import json

from app.db.session import init_db
from app.services.scraper import list_scrape_runs, run_scrape


def _cmd_scrape(args: argparse.Namespace) -> int:
    run_id = run_scrape(full_trace=args.full_trace)
    print(f"scrape_run_id={run_id}")
    return 0


def _cmd_scrape_runs(args: argparse.Namespace) -> int:
    runs = list_scrape_runs(limit=args.limit)
    payload = [
        {
            "id": r.id,
            "status": r.status,
            "started_at": r.started_at.isoformat(),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "error_type": r.error_type,
            "error_message": r.error_message,
        }
        for r in runs
    ]
    print(json.dumps(payload, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="gestion-satisfactory-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scrape = subparsers.add_parser("scrape", help="Scrape wiki and update DB catalogs")
    scrape.add_argument("--full-trace", action="store_true", help="Raise exceptions with full traceback")
    scrape.set_defaults(func=_cmd_scrape)

    scrape_runs = subparsers.add_parser("scrape-runs", help="List recent scrape runs")
    scrape_runs.add_argument("--limit", type=int, default=20)
    scrape_runs.set_defaults(func=_cmd_scrape_runs)

    args = parser.parse_args()
    init_db()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
