from __future__ import annotations

from pathlib import Path

import pytest

from clusdr import ClusdrError
from clusdr._options import Options
from clusdr._tls import client_credentials, cn_from_pem

# Subject CN=node-a (UTF8String). Expiry is irrelevant; we only parse the name.
_NODE_A_CERT = b"""-----BEGIN CERTIFICATE-----
MIIBmTCCAT+gAwIBAgIUQcxWr82x7fO3L8Jl+Gdnhg2XsrQwCgYIKoZIzj0EAwIw
IjEPMA0GA1UECgwGY2x1c2RyMQ8wDQYDVQQDDAZub2RlLWEwHhcNMjYwOTEyMDk0
MjE0WhcNMjYwOTEzMDk0MjE0WjAiMQ8wDQYDVQQKDAZjbHVzZHIxDzANBgNVBAMM
Bm5vZGUtYTBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABPT6vDCA4Rz1uoJqDDRn
Oek6f1d/DUKHL6EphIpdG7Nt5G8BflHU0EorNZp5mU0T+NHkF88RjUOQdXO9N58d
Q5yjUzBRMB0GA1UdDgQWBBRRcJ28BTllqHsVyBLoyIiEIhvrgTAfBgNVHSMEGDAW
gBRRcJ28BTllqHsVyBLoyIiEIhvrgTAPBgNVHRMBAf8EBTADAQH/MAoGCCqGSM49
BAMCA0gAMEUCIBSuV03b6SI3b0La8HerkVb4jsDiKG711hB8jhV/X6v1AiEAsMIB
70nN7/saTVsIuZDacHOF+kM+mYqPN33lUdIukXk=
-----END CERTIFICATE-----
"""


def test_cn_from_pem() -> None:
    assert cn_from_pem(_NODE_A_CERT) == "node-a"


def test_missing_certs_error(tmp_path: Path) -> None:
    with pytest.raises(ClusdrError, match="TLS enabled"):
        client_credentials(Options(addr="127.0.0.1:1", data_dir=str(tmp_path)))
