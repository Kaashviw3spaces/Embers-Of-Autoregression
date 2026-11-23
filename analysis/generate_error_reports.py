"""Compatibility command using the single audited evidence pipeline."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main(runs_dir='runs', output_dir='analysis'):
    from rebuild_evidence import main as rebuild, ROOT
    if Path(runs_dir).resolve() != (ROOT/'runs').resolve():
        raise ValueError('Import new evidence into runs/ before rebuilding; arbitrary directories are not silently ignored.')
    return rebuild()


if __name__ == '__main__':
    main()
