"""Build the actual review queue; never mark automated annotations as manual."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

if __name__ == '__main__':
    from rebuild_evidence import main
    main()
