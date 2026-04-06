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

"""Stable exception types for the lantern-grammar package.

These exceptions are part of the compatibility-governed public contract.
See DN-LGR-PROP-004 for the full exception contract.
"""


class LanternGrammarLoadError(Exception):
    """Raised when the Lantern Grammar model cannot be loaded.

    Returned by construction methods (``Grammar.load()`` and
    ``Grammar.from_directory()``) when model data is absent, unloadable, or
    structurally invalid.

    Subclasses may be introduced in later minor versions for more specific
    failure modes; they are always catchable as ``LanternGrammarLoadError``.

    Example::

        from lantern_grammar import Grammar, LanternGrammarLoadError

        try:
            grammar = Grammar.load()
        except LanternGrammarLoadError as exc:
            raise RuntimeError("Could not load Lantern Grammar") from exc
    """
