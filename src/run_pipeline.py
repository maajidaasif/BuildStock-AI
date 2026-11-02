
import subprocess
import sys
from pathlib import Path

# BuildStock AI - Module 10
# End-to-End Pipeline Integration

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

MODULES = [
    "create_dataset.py",
    "validate_dataset.py",
    "analyze_inventory.py",
    "decision_engine.py",
    "reorder_recommendation.py",
    "ai_inventory_explanation.py",
    "inventory_alerts.py",
    "system_tests.py",
]


def run_pipeline():
    print("=" * 65)
    print("BUILDSTOCK AI - MODULE 10")
    print("END-TO-END PIPELINE INTEGRATION")
    print("=" * 65)

    if not SRC.exists():
        print(f"ERROR: Source directory not found: {SRC}")
        return 1

    # Check all module files before running anything.
    missing_modules = [
        module for module in MODULES
        if not (SRC / module).is_file()
    ]

    if missing_modules:
        print("\nERROR: The following module files are missing:")
        for module in missing_modules:
            print(f"  - {module}")

        print("\nCheck the filenames inside your src folder.")
        return 1

    for index, module in enumerate(MODULES, start=1):
        module_path = SRC / module

        print(f"\n[{index}/{len(MODULES)}] Running: {module}")
        print("-" * 65)

        try:
            result = subprocess.run(
                [sys.executable, "-u", str(module_path)],
                cwd=str(ROOT),
                check=False,
            )
        except OSError as error:
            print(f"\nERROR: Could not start {module}: {error}")
            return 1

        if result.returncode != 0:
            print(f"\nFAILED: {module}")
            print(f"Exit code: {result.returncode}")
            print("Fix this module's error before continuing.")
            return result.returncode or 1

        print(f"\nSUCCESS: {module}")

    print("\n" + "=" * 65)
    print("ALL PIPELINE MODULES COMPLETED SUCCESSFULLY")
    print(f"Modules completed: {len(MODULES)}")
    print(f"Project directory: {ROOT}")
    print(f"CSV output directory: {ROOT / 'data'}")
    print("=" * 65)
    print(
        "Note: AI explanations and reorder quantities are suggestions. "
        "Review them before purchasing."
    )

    return 0


if __name__ == "__main__":
    sys.exit(run_pipeline())
