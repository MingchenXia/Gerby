"""Export the Foundations contribution using the shared Gerby adapter."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

if __name__ == "__main__":
    export(Path(sys.argv[1]), Path(sys.argv[2]))
