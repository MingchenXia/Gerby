"""Export only the active reading manuscript from the private research repository."""
from pathlib import Path
import sys
from common import configure, export

if __name__ == "__main__":
    configure("non-kahler-pluripotential-theory", "Singularities in Hermitian pluripotential theory", "https://github.com/MingchenXia/non-kahler-pluripotential-theory", author="AI-assisted working research draft", directory="book", bibliography="references.bib")
    export(Path(sys.argv[1]), Path(sys.argv[2]))
