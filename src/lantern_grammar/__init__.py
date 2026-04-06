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

"""lantern-grammar — authoritative semantic model for Lantern governed workflow.

Public stable exports
---------------------
* :class:`Grammar` — read-only projection of the Lantern Grammar model.
* :exc:`LanternGrammarLoadError` — raised when the model cannot be loaded.

Canonical import pattern::

    from lantern_grammar import Grammar, LanternGrammarLoadError

See the project README and decision note DN-LGR-PROP-004 for the full
compatibility-governed API contract.
"""

from ._exceptions import LanternGrammarLoadError
from ._grammar import Grammar

__all__ = ["Grammar", "LanternGrammarLoadError"]
