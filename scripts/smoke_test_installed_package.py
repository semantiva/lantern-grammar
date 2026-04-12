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

"""Exercise the installed lantern-grammar distribution from a clean environment."""

from __future__ import annotations

import argparse

from lantern_grammar import Grammar


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-package-version")
    parser.add_argument("--expected-model-version")
    args = parser.parse_args()

    grammar = Grammar.load()
    manifest = grammar.manifest()
    report = grammar.validate_integrity()
    entity = grammar.get_entity("lg:artifacts/ch")
    term = grammar.get_term("lg:vocab/term_ch")
    dependencies = grammar.gate_dependencies("lg:gates/gt_115")

    if args.expected_package_version and grammar.package_version() != args.expected_package_version:
        raise SystemExit(
            f"Expected package version {args.expected_package_version!r}, got {grammar.package_version()!r}"
        )

    if args.expected_model_version and manifest["model_version"] != args.expected_model_version:
        raise SystemExit(f"Expected model version {args.expected_model_version!r}, got {manifest['model_version']!r}")

    if not report["ok"]:
        raise SystemExit(f"Installed grammar integrity check failed: {report['errors']}")
    if entity is None:
        raise SystemExit("Installed grammar is missing lg:artifacts/ch")
    if term is None:
        raise SystemExit("Installed grammar is missing lg:vocab/term_ch")
    if not dependencies["requires_input"]:
        raise SystemExit("Installed grammar returned no GT-115 input dependencies")

    print("Installed package smoke test passed.")
    print(f"Package version: {grammar.package_version()}")
    print(f"Model version: {manifest['model_version']}")
    print(f"GT-115 inputs: {', '.join(dependencies['requires_input'])}")


if __name__ == "__main__":
    main()
