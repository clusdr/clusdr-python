"""Application SDK for the local Clusdr daemon.

Applications talk only to the daemon on the same host (Docker-style).
The daemon is the cluster member; this package does not dial other nodes.

    from clusdr import local

    cluster = local()
    members = cluster.members()
    cluster.publish("deployment", {"sha": "abc"})
    for event in cluster.watch():
        ...
"""

from clusdr._client import Cluster, Event, Member, dial, local
from clusdr._coord import Lease, Lock
from clusdr._errors import ClusdrError

__all__ = [
    "Cluster",
    "ClusdrError",
    "Event",
    "Lease",
    "Lock",
    "Member",
    "dial",
    "local",
]
