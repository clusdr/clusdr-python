"""Application SDK for the local Clusdr daemon.

The application is not a cluster member. It dials the daemon on this host
the same way a process talks to a local Docker engine. This package never
dials other nodes and never joins Raft.

    your process  ──►  clusdr daemon on this host  ──►  the rest of the cluster

Install::

    pip install clusdr

A running daemon is required (``clusdr init && clusdr start --bootstrap``).
``local()`` dials ``CLUSDR_GRPC_ADDR`` or ``127.0.0.1:7947`` and waits on
Health. ``dial(addr)`` is for tests and a second daemon on this host — not a
remote peer.

    from clusdr import local

    with local() as c:
        members = c.members()
        c.publish("deployment", {"sha": "abc"})
        lk = c.lock("scheduler", ttl=15)
        try:
            _ = lk.token
        finally:
            c.unlock("scheduler")
        for event in c.watch(topics=["deployment"]):
            ...

TLS is on unless ``insecure=True`` or ``CLUSDR_TLS=disabled``. Missing PEMs
are an error (no skip-verify fallback). Unary calls retry UNAVAILABLE /
ABORTED / RESOURCE_EXHAUSTED. One ``watch()`` loop per client.

Walkthrough: https://clusdr.io/docs/sdk/python
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
