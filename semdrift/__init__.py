"""Source-tree entry point; supports python -m semdrift.cli without installation."""
from pathlib import Path
__path__ = [str(Path(__file__).resolve().parent.parent / 'src' / 'semdrift')]
