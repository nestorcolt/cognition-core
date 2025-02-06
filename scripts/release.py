"""

# Make sure you're on main branch and everything is committed
git checkout main
git pull origin main

# Run the release script for your first version (0.1.0)
python scripts/release.py minor

# This will:
# 1. Check you're on main branch
# 2. Check working directory is clean
# 3. Pull latest changes
# 4. Bump version (using bump_version.py)
# 5. Commit the changes
# 6. Create an annotated tag
# 7. Push everything to GitHub

"""

import subprocess
import sys
from bump_version import bump_version


def run_command(command):
    process = subprocess.run(command, shell=True, text=True, capture_output=True)
    if process.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error: {process.stderr}")
        return False
    return True


def release(version_type):
    # Ensure we're on main branch
    result = subprocess.run(
        "git rev-parse --abbrev-ref HEAD", shell=True, text=True, capture_output=True
    )
    if result.stdout.strip() != "main":
        print("Must be on main branch to release")
        return False

    # Ensure working directory is clean
    if not run_command("git diff-index --quiet HEAD --"):
        print("Working directory must be clean")
        return False

    # Pull latest changes
    if not run_command("git pull origin main"):
        return False

    # Bump version using our existing bump_version.py
    try:
        new_version = bump_version(version_type)
    except ValueError as e:
        print(f"Error bumping version: {e}")
        return False

    # Commit and tag
    if not all(
        [
            run_command("git add ."),
            run_command(f'git commit -m "bump: version {new_version}"'),
            run_command(
                f'git tag -a v{new_version} -m "Release version {new_version}"'
            ),
            run_command("git push origin main --tags"),
        ]
    ):
        return False

    print(f"Successfully released version {new_version}")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["major", "minor", "patch"]:
        print("Usage: python release.py [major|minor|patch]")
        sys.exit(1)

    success = release(sys.argv[1])
    sys.exit(0 if success else 1)
