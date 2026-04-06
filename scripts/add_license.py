#!/usr/bin/env python3

# Copyright 2025 Lantern Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Add Apache 2.0 license headers to all Python files in the project."""

import os

from scripts import HEADER, HEADER_PATTERN, INCLUDE_DIRS, EXTENSIONS


def add_header(filepath: str) -> bool:
    """Add license header to a file if it doesn't already exist."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if HEADER_PATTERN.search(content):
        return False  # Header already exists

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(HEADER + "\n" + content)
    return True


def main() -> None:
    """Batch add license headers to all Python files."""
    added_count = 0

    for dirpath in INCLUDE_DIRS:
        if not os.path.exists(dirpath):
            continue
        for root, _, files in os.walk(dirpath):
            for filename in files:
                if any(filename.endswith(ext) for ext in EXTENSIONS):
                    fullpath = os.path.join(root, filename)
                    if add_header(fullpath):
                        print(f"✅ Added header: {fullpath}")
                        added_count += 1
                    else:
                        print(f"⏭️  Already has header: {fullpath}")

    print("\n✅ License header addition complete.")
    print(f"Total files updated: {added_count}")


if __name__ == "__main__":
    main()
