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


def run_gate(tmp_path, rows, *extra):
    manifest = tmp_path / 'manifest.csv'
    manifest.write_text('path,label,split\n' + ''.join(f'photos/x{i}.jpg,unknown,heldout\n' for i in range(rows)))
    return subprocess.run([sys.executable, str(ROOT/'eval/run.py'), '--manifest', str(manifest), '--dry-run', *extra],
                          capture_output=True, text=True)


def test_small_photo_sets_need_the_explicit_spot_check_flag(tmp_path):
    result = run_gate(tmp_path, 8)
    assert result.returncode == 2 and 'Supply 30–50' in result.stderr


def test_spot_checks_only_evaluate_frozen_settings(tmp_path):
    result = run_gate(tmp_path, 8, '--spot-check', '--split', 'dev')
    assert result.returncode == 2 and 'only evaluates frozen settings' in result.stderr


def test_spot_checks_stay_small(tmp_path):
    result = run_gate(tmp_path, 3, '--spot-check')
    assert result.returncode == 2 and '5–29 photos' in result.stderr
