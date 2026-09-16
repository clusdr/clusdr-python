<h1 align="center">
  <a href="https://clusdr.io/docs/sdk/python">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/clusdr/clusdr-python/main/assets/python-lettermark-dark.svg">
      <img src="https://raw.githubusercontent.com/clusdr/clusdr-python/main/assets/python-lettermark.svg" alt="clusdr Python" width="160" height="164">
    </picture>
  </a>
</h1>

<p align="center">A runtime for the cluster. An SDK for the app.</p>

<p align="center">
  <a href="https://clusdr.io/docs/sdk/python"><img src="https://img.shields.io/badge/docs-clusdr.io-0C0C10" alt="docs"></a>
  <a href="https://pypi.org/project/clusdr/"><img src="https://img.shields.io/pypi/v/clusdr" alt="PyPI"></a>
  <a href="https://github.com/clusdr/clusdr-python/actions/workflows/ci.yml"><img src="https://github.com/clusdr/clusdr-python/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/clusdr/clusdr-python/blob/main/pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+"></a>
  <a href="https://github.com/clusdr/clusdr-python/blob/main/LICENSE"><img src="https://img.shields.io/github/license/clusdr/clusdr-python" alt="License"></a>
</p>

Application SDK for the **local** Clusdr daemon. This package does not join the cluster.

```text
your process  ──►  clusdr daemon on this host  ──►  the rest of the cluster
```

Not a database, queue, or Kubernetes. Wire API is **v1alpha1**. TLS is on by default.

## Install

```bash
pip install clusdr
```

CPython 3.10+. Same version train as the daemon.

A running daemon on this host is required:

```bash
curl -fsSL https://clusdr.io/install.sh | sh
```

Linux amd64/arm64, or [Docker Hub `durguto/clusdr`](https://hub.docker.com/r/durguto/clusdr) (GHCR: `ghcr.io/clusdr/clusdr`). Then `clusdr init` and `clusdr start --bootstrap`. Guide: [first member](https://clusdr.io/docs/guide/first-member).

## Use

`local()` dials `CLUSDR_GRPC_ADDR` or `127.0.0.1:7947`, waits on Health, then you own the connection.

```python
from clusdr import local

with local() as c:
    members = c.members()
    leader = c.leader()

    c.publish("deployment", {"sha": "abc"})

    lk = c.lock("scheduler", ttl=15)
    try:
        _ = lk.token
    finally:
        c.unlock("scheduler")

    for event in c.watch():
        # member.join, leader.changed, custom.deployment, …
        ...

    for event in c.watch(topics=["deployment"]):
        # only custom.deployment (no membership snapshot)
        ...
```

`dial` is for tests and operators. Apps use `local()`.

One `Cluster` is safe for unary calls from several threads. Same connection = same holder (`unlock` is process-wide for that name). One `watch()` iterator per client.

`ttl` is seconds. Leaving `with` (or `close()`) stops Watch, unlocks, and revokes what this process still holds. Failures raise `ClusdrError`.

Full surface: [Python SDK](https://clusdr.io/docs/sdk/python).

## TLS

On unless `insecure=True` or `CLUSDR_TLS=disabled`. PEMs (`ca.crt`, `node.crt`, `node.key`) come from `data_dir`, `CLUSDR_DATA_DIR`, or `~/.clusdr`. Missing files are an error; this client does not skip-verify.

## Not in this package

- Join, promote, or configure the cluster (CLI)
- Async / `asyncio`
- Talking to a remote node's Runtime API as the normal path — put a daemon on that host

## Links

- **Docs:** [clusdr.io](https://clusdr.io) · [Python SDK](https://clusdr.io/docs/sdk/python) · [from your app](https://clusdr.io/docs/guide/from-your-app)
- **Daemon:** [github.com/clusdr/clusdr](https://github.com/clusdr/clusdr)
- **This repo:** [github.com/clusdr/clusdr-python](https://github.com/clusdr/clusdr-python)

Apache-2.0. Contributor checkout (editable + proto regen): [CONTRIBUTING.md](https://github.com/clusdr/clusdr-python/blob/main/CONTRIBUTING.md).
