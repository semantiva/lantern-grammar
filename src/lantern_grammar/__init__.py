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
