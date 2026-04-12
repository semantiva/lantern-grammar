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

"""Validate the package-version source and its current model-version alignment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib  # type: ignore
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        import tomllib  # type: ignore


def _load_pyproject(pyproject_path: Path) -> dict:
    return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))


def _package_version(pyproject_data: dict) -> str:
    project = pyproject_data.get("project", {})
    version = project.get("version")
    if not isinstance(version, str) or not version:
        raise SystemExit("pyproject.toml must define a static [project].version string")
    return version


def _dynamic_version_present(pyproject_data: dict) -> bool:
    dynamic = pyproject_data.get("tool", {}).get("setuptools", {}).get("dynamic", {})
    return "version" in dynamic


def _model_version(manifest_path: Path) -> str:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = manifest.get("model_version")
    if not isinstance(version, str) or not version:
        raise SystemExit("model/manifest.json must define a model_version string")
    return version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pyproject", default="pyproject.toml")
    parser.add_argument("--manifest", default="model/manifest.json")
    parser.add_argument("--require-package-model-equality", action="store_true")
    parser.add_argument("--print-package-version", action="store_true")
    parser.add_argument("--print-model-version", action="store_true")
    args = parser.parse_args()

    pyproject_path = Path(args.pyproject)
    manifest_path = Path(args.manifest)
    pyproject_data = _load_pyproject(pyproject_path)
    package_version = _package_version(pyproject_data)
    model_version = _model_version(manifest_path)

    if args.print_package_version:
        print(package_version)
        return

    if args.print_model_version:
        print(model_version)
        return

    if _dynamic_version_present(pyproject_data):
        raise SystemExit("pyproject.toml must not define tool.setuptools.dynamic.version")

    print(f"Package version source: {pyproject_path} -> [project].version = {package_version}")
    print(f"Model version source: {manifest_path} -> model_version = {model_version}")

    if args.require_package_model_equality and package_version != model_version:
        raise SystemExit(
            "The current first-release publish posture requires package version "
            f"{package_version!r} to equal model version {model_version!r}"
        )

    print("Version alignment checks passed.")


if __name__ == "__main__":
    main()
