"""Export the active SGPT manuscript without modifying its source."""
from pathlib import Path
import sys
from common import configure, export

if __name__ == "__main__":
    configure("sgpt", "Singularities in global pluripotential theory", "https://github.com/MingchenXia/SGPT")
    export(Path(sys.argv[1]), Path(sys.argv[2]))
