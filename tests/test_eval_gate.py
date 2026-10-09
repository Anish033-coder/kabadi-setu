import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_bedrock_requires_access_confirmation_before_reading_any_photos():
    result = subprocess.run([sys.executable, str(ROOT/'eval/run.py'), '--provider', 'bedrock',
                             '--allow-paid-calls', '--manifest', '/missing.csv'],
                            capture_output=True, text=True)
    assert result.returncode == 2
    assert 'Bedrock remains blocked' in result.stderr
    assert 'FileNotFoundError' not in result.stderr
