"""Compatibility command. Source groups and uncertainties are never hidden."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def generate_comparison_report(*args, **kwargs):
    from rebuild_evidence import main, ROOT
    main()
    return str(ROOT/'MODEL_COMPARISON.md')


if __name__ == '__main__':
    generate_comparison_report()
