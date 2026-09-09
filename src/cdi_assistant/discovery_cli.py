from __future__ import annotations

import argparse
import json
from pathlib import Path

from .discovery.engine import DiscoveryEngine
from .discovery.sources.france_travail import FranceTravailConfig, FranceTravailSource
from .discovery.storage import JobDiscoveryStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / "data" / "jobs.db"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover France Data/AI CDI offers from configured sources."
    )
    parser.add_argument(
        "--source",
        choices=["france-travail"],
        default="france-travail",
        help="Discovery provider to use.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="SQLite database used to persist discovered offers.",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=None,
        help="Override the generated query portfolio size.",
    )
    args = parser.parse_args()

    config = None
    if args.max_queries is not None:
        from dataclasses import replace
        from .discovery.config import DiscoveryConfig

        config = replace(DiscoveryConfig(), max_queries=max(1, args.max_queries))

    if args.source == "france-travail":
        source = FranceTravailSource(FranceTravailConfig.from_environment())
    else:  # pragma: no cover - argparse prevents this branch
        raise RuntimeError(f"Unsupported source: {args.source}")

    store = JobDiscoveryStore(args.db)
    run = DiscoveryEngine([source], store=store, config=config).run()
    print(
        json.dumps(
            {
                "queries": len(run.queries),
                "newly_discovered_in_run": len(run.jobs),
                "persisted": run.persisted,
                "database": str(args.db),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
