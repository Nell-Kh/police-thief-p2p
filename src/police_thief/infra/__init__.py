"""Infrastructure adapters: MCP transport, language-model providers, email.

Only the dependency-free transport primitives are re-exported; ``PeerClient``
and the MCP server are imported from their own modules to keep this package's
import graph acyclic.
"""

from .transport import LoopbackTransport, Transport, TransportError

__all__ = ["LoopbackTransport", "Transport", "TransportError"]
