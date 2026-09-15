# clusdr (Python)

Application SDK for the **local** Clusdr daemon. This package does not join the cluster.

<p>
  <a href="https://github.com/durguto/clusdr-python/actions/workflows/ci.yml"><img src="https://github.com/durguto/clusdr-python/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/durguto/clusdr-python/blob/main/pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+"></a>
  <a href="https://github.com/durguto/clusdr-python/releases"><img src="https://img.shields.io/github/v/release/durguto/clusdr-python" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/durguto/clusdr-python" alt="License"></a>
</p>


```python
from clusdr import local

c = local()
members = c.members()
c.publish("deployment", {"sha": "abc"})
lk = c.lock("scheduler", ttl=15)
c.unlock("scheduler")
```

Requires a running daemon.

```bash
pip install clusdr
```

Same version train as the daemon (first release: `0.1.0`). Python 3.10+. Product docs: [Python SDK](https://clusdr.io/docs/sdk/python). Apache-2.0.

Contributor checkout (editable + proto regen): see [CONTRIBUTING.md](CONTRIBUTING.md).
