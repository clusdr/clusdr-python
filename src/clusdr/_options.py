"""Environment defaults. Applications talk to the same-host daemon."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ADDR = "127.0.0.1:7947"
DEFAULT_REQUEST_TIMEOUT = 10.0
DEFAULT_READY_TIMEOUT = 10.0
MAX_BACKOFF = 2.0
INITIAL_BACKOFF = 0.05
MAX_PAYLOAD = 64 * 1024

CA_FILE = "ca.crt"
CERT_FILE = "node.crt"
KEY_FILE = "node.key"


@dataclass
class Options:
    addr: str
    insecure: bool = False
    data_dir: str = ""
    holder: str = ""
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT
    ready_timeout: float = DEFAULT_READY_TIMEOUT
    server_name: str = ""


def env_addr() -> str:
    v = os.environ.get("CLUSDR_GRPC_ADDR", "").strip()
    return v or DEFAULT_ADDR


def env_insecure() -> bool:
    v = os.environ.get("CLUSDR_TLS", "").strip().lower()
    return v in ("disabled", "off", "false", "0")


def env_data_dir() -> str:
    v = os.environ.get("CLUSDR_DATA_DIR", "").strip()
    if v:
        return v
    return str(Path.home() / ".clusdr")


def env_server_name() -> str:
    return os.environ.get("CLUSDR_TLS_SERVER_NAME", "").strip()
