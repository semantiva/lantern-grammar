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

"""Setuptools build hooks for packaging the Lantern Grammar model bundle."""

from __future__ import annotations

import importlib
import shutil
from pathlib import Path

setup = importlib.import_module("setuptools").setup
_build_py = importlib.import_module("setuptools.command.build_py").build_py


class build_py(_build_py):  # type: ignore[name-defined,valid-type,misc]
    """Copy the authoritative model bundle into the built wheel."""

    def run(self) -> None:
        super().run()

        source_dir = Path(__file__).parent / "model"
        if not source_dir.is_dir():
            raise FileNotFoundError(f"Model directory not found: {source_dir}")

        target_dir = Path(self.build_lib) / "lantern_grammar" / "_model"
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(source_dir, target_dir)

        self._copied_model_files = [str(path) for path in target_dir.rglob("*") if path.is_file()]

    def get_outputs(self, include_bytecode: bool = True) -> list[str]:
        outputs = super().get_outputs(include_bytecode=include_bytecode)
        return outputs + getattr(self, "_copied_model_files", [])


setup(cmdclass={"build_py": build_py})
