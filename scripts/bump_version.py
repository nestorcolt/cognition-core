import re
import sys
from pathlib import Path


def bump_version(version_type):
    init_file = Path("src/cognition_core/__init__.py")
    content = init_file.read_text()

    # Extract current version
    version_match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
    if not version_match:
        raise ValueError("Version not found in __init__.py")

    current_version = version_match.group(1)
    major, minor, patch = map(int, current_version.split("."))

    # Bump version
    if version_type == "major":
        major += 1
        minor = patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    elif version_type == "patch":
        patch += 1
    else:
        raise ValueError("Invalid version type. Use 'major', 'minor', or 'patch'")

    new_version = f"{major}.{minor}.{patch}"

    # Update file
    new_content = re.sub(
        r'__version__ = ["\']([^"\']+)["\']', f'__version__ = "{new_version}"', content
    )
    init_file.write_text(new_content)

    print(f"Bumped version from {current_version} to {new_version}")
    return new_version


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["major", "minor", "patch"]:
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)

    bump_version(sys.argv[1])
