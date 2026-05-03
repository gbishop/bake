import os
import subprocess
from pathlib import Path

# --- CONFIGURATION ---
FOLDER_PATH = "./recipes"  # Path to your recipe files
BAKE_SCRIPT = "bake.py"  # The script you want to run
# ---------------------


def run_batch_test():
    folder = Path(FOLDER_PATH)

    if not folder.is_dir():
        print(f"Error: Folder '{FOLDER_PATH}' not found.")
        return

    files = list(folder.glob("*.bake"))

    print(f"Checking {len(files)} files...\n" + "-" * 30)

    for recipe_file in files:
        try:
            # We run the script and wait for it to finish
            # capture_output=True keeps the bake script's print statements out of your terminal
            result = subprocess.run(
                ["python", BAKE_SCRIPT, str(recipe_file)],
                capture_output=True,
                text=True,
            )

            # Check if it returned a non-zero exit code
            if result.returncode != 0:
                print(f"❌ FAILED: {recipe_file.name} (Exit code: {result.returncode})")
                # Optional: Print the specific error from the crashed script
                # print(f"   Error: {result.stderr.strip()}")

        except Exception as e:
            # This catches system-level failures (e.g., Python not found)
            print(f"💥 CRASHED: {recipe_file.name} (System Error: {e})")


if __name__ == "__main__":
    run_batch_test()
