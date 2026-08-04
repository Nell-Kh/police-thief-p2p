"""Police-Thief P2P: distributed cops-and-robbers over a peer-to-peer network.

Two symmetric autonomous peers (cop and thief) race on a discrete grid with no
central server and no referee. Integrity is enforced cryptographically via
SHA-256 commit-reveal; uncertainty is modelled with decaying pheromone scent
fields and Bayesian belief maps.

University of Haifa, "Orchestration of AI Agents", final project 2026.
"""

from .shared.version import __version__

__all__ = ["__version__"]
