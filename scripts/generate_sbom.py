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

"""Generate a software bill of materials (SBOM) in SPDX JSON format."""

import subprocess
from pathlib import Path


def generate_sbom() -> None:
    """Generate SBOM using cyclonedx-bom."""
    output = Path("sbom.spdx.json")
    cmd = ["cyclonedx-bom", "--output-format", "json", "--output-file", str(output)]
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ SBOM generated: {output}")
    except FileNotFoundError:
        print("❌ cyclonedx-bom not found. Install with: pip install cyclonedx-bom")
        raise
    except subprocess.CalledProcessError as e:
        print(f"❌ SBOM generation failed: {e}")
        raise


if __name__ == "__main__":
    generate_sbom()
