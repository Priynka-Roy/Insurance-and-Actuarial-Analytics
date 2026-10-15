"""Run the full offline analysis on downloaded official raw datasets."""
import os
import sys
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from actuarylab.pipeline import run  # noqa: E402

if __name__ == '__main__':
    run()
