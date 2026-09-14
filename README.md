# clusdr (Python)

Application SDK for the **local** Clusdr daemon. This package does not join the cluster.

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

Same version train as the daemon (first release: `0.1.0`). Python 3.10+. Product docs: [Python SDK](https://clusdr.io/docs/sdk/python).

Contributor checkout (editable + proto regen):

```bash
pip install -e ".[dev]"
make proto    # from proto next to this tree
pytest
```
