"""Compatibility importer; no invented timing, usage, or success claims."""
from datetime import datetime, timezone
import json
from pathlib import Path
from analysis.evidence import redact


def create_experiment_run_package(run_data_list, task_type="acronym", output_base="results"):
    from rebuild_evidence import ROOT, main
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    for index,run in enumerate(run_data_list):
        path=ROOT/'runs'/f'imported_{stamp}_{index}.json'
        path.write_text(json.dumps(redact(run),indent=2),encoding='utf-8')
    main()
    return str(ROOT/'results/master')
