import subprocess
import sys
import pathlib

SCRIPTS_DIR = pathlib.Path(__file__).parent
PYTHON = pathlib.Path(__file__).resolve().parents[1] / ".venv" / "bin" / "python"

SCRIPTS = [
    "1-packaging.py",
    "2-add-models.py",
    "3-model-resource.py",
    "4-model-components.py",
]

failed = []

for script in SCRIPTS:
    path = SCRIPTS_DIR / script
    print(f"\n{'=' * 60}")
    print(f"  Running: {script}")
    print(f"{'=' * 60}\n")

    result = subprocess.run(
        [str(PYTHON), str(path)],
        cwd=str(SCRIPTS_DIR),
        timeout=300,
    )

    if result.returncode != 0:
        failed.append(script)
        print(f"\n  FAILED: {script} (exit code {result.returncode})")
    else:
        print(f"\n  PASSED: {script}")

print(f"\n{'=' * 60}")
if failed:
    print(f"  FAILURES: {', '.join(failed)}")
    sys.exit(1)
else:
    print("  ALL ML DOCUMENTATION TESTS PASSED")
    sys.exit(0)
